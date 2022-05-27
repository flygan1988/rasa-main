from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action
from rasa_sdk import utils
from utils.constants import (
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_USER,
    MYSQL_DBNAME,
    RECOM_PARAMS,
    RECOM_SLOT_MAP,
    RECOM_UTTER_MAP,
    RECOM_CHI_MAP,
    SLOT_LISTED_OBJECTS,
    SLOT_RECO_HIS
)
from reco.reco_main import reco_car_model

from knowledgebase.car_knowledgebase import CarKnowledgeBase
import logging


logger = logging.getLogger(__name__)


class ActionSuggestCar(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db=MYSQL_DBNAME, user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["level_name"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_suggest_car"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        logger.info("Enter action: %s", self.name())
        car_list = tracker.get_slot('car')
        model_name = tracker.get_slot('model_name')
        favor = tracker.get_slot('favor')
        model_id = tracker.get_slot('curr_model')
        logger.info("curr_model = %s", model_id)
        latest_intent = tracker.get_intent_of_latest_message()
        params = {}
        for slot in RECOM_PARAMS:
            value = tracker.get_slot(RECOM_SLOT_MAP[slot])
            if type(value) == list:
                params[slot] = value
            else:
                params[slot] = [value] if value is not None else []
        logger.info("recommend params = %s", [params])
        rmd_rst, rst_dsc, rst_flag = reco_car_model([params], {})
        logger.info("rmd_rst = %s", rmd_rst)
        logger.info("rst_dsc = %s", rst_dsc)
        logger.info("rst_flag = %s", rst_flag)
        res = rmd_rst[0]
        dispatcher.utter_message(text=f"好的，确认你要看的车系是：{car_list}， 车型是：{model_name}，车型偏好是：{favor}")
        if latest_intent != 'one_desire_car' and model_id is not None:
            curr_model = await utils.call_potential_coroutine(self.knowledge_base.get_object(model_id))
            curr_model = curr_model[0]
            if curr_model['model_intr'] is not None and len(curr_model['model_intr']) != 0:
                dispatcher.utter_message(text=curr_model['model_intr'],
                                         image="http://dongguan.41mc.com/uploads/allimg/211105/16243T511-0.jpg")
            else:
                curr_series = await utils.call_potential_coroutine(self.knowledge_base.get_series_intr(curr_model['series_id']))
                curr_series = curr_series[0]
                dispatcher.utter_message(text=curr_series['series_intr'],
                                         image="http://dongguan.41mc.com/uploads/allimg/211105/16243T511-0.jpg")
        else:
            if len(res) == 0:
                dispatcher.utter_message(text="抱歉，没有相关车型推荐")
            else:
                buttons = []
                for i, reco_model in enumerate(res):
                    button = {'title': reco_model['model_name'], 'payload': '/affirm{"curr_model":"'+reco_model['model_id']+'"}'}
                    buttons.append(button)
                tag = rst_dsc[0]['tag']
                dsc = rst_dsc[0]['dsc']
                utter = RECOM_UTTER_MAP[tag]
                tmp_str = ",".join([RECOM_CHI_MAP[p] for p in dsc])
                utter = utter.format(tmp_str)
                dispatcher.utter_message(text=utter, buttons=buttons)
                dispatcher.utter_message(text="给您推荐以上车型，请点击车型按钮了解该款车详情")
        # dispatcher.utter_message(response="utter_dealer_detail")
        return [SlotSet('car', None)] + [SlotSet(RECOM_SLOT_MAP[slot], None) for slot in RECOM_PARAMS]

