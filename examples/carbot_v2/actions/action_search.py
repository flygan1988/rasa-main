from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet, EventType, ActionExecuted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action
from rasa_sdk import utils
from utils.constants import (
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_USER,
    MYSQL_DBNAME
)
from knowledgebase.car_knowledgebase import CarKnowledgeBase
import logging


logger = logging.getLogger(__name__)


class SerchAction(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db=MYSQL_DBNAME, user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["level_name"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_search"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        logger.info("Enter action: %s", self.name())
        latest_intent = tracker.get_intent_of_latest_message()
        car_list = tracker.get_slot('car')
        logger.info("car_list = %s", car_list)
        model_name = tracker.get_slot('model_name')
        logger.info("model_name = %s", model_name)
        mention = tracker.get_slot('mention')
        logger.info("mention = %s", mention)

        if car_list is None or len(car_list) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到车系信息")
            return [SlotSet('mention', None)]
        series_name = car_list[0]
        series_name_list = await utils.call_potential_coroutine(self.knowledge_base.get_series_names(series_name))

        if len(series_name_list) > 1 and (latest_intent == 'one_desire_car'
                                          or latest_intent == 'ask_car_attribute'):
            buttons = []
            # dispatcher.utter_message(text="发现以下相似车系，请点击你想看的车系按钮：")
            for i, obj in enumerate(series_name_list, 1):
                button = {}
                button['title'] = obj['series_name']
                button['payload'] = '/inform_series{"car":["' + obj['series_name'] + '"]}'
                buttons.append(button)
            dispatcher.utter_message(text="发现以下相似车系，请点击你想看的车系按钮：", buttons=buttons)
            return []
        else:
            if series_name_list is not None and len(series_name_list) != 0:
                series_name = series_name_list[0]['series_name']
            dispatcher.utter_message(text="以下是在售车型")
            models = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name))
            if model_name is not None:
                models = list(filter(lambda model: model_name in model['model_name'], models))
            if models is None or len(models) == 0:
                dispatcher.utter_message(text="抱歉，未找到相关车型")
                return [SlotSet('model_name', None)]
            # if len(models) == 1:
            #     model_id = models[0]['model_id']
            #     return [SlotSet('curr_model', model_id), ActionExecuted('action_car_attribute')]
            buttons = []
            for i, model in enumerate(models, 1):
                trim_name = model['trim_name'].replace(" ", "")
                model_id = model['model_id']
                button = {}
                button['title'] = model['model_name']
                button['payload'] = '/inform_model{"model_name":"'+ trim_name +'", "curr_model":"'+ model_id +'"}'
                buttons.append(button)

            dispatcher.utter_message(text="请问您想看哪个车型？", buttons=buttons)
            return []
