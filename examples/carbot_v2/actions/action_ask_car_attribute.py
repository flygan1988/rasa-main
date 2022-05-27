from typing import Text, Dict, List, Any
import sys
sys.path.append("../")
from rasa_sdk import Action
from rasa_sdk import utils
from rasa_sdk.events import SlotSet

from utils.constants import (
MYSQL_PASSWORD,
MYSQL_HOST,
MYSQL_DBNAME,
MYSQL_USER,
SLOT_MENTION,
SLOT_MODEL_NAME,
SLOT_ATTRIBUTE_LIST,
SLOT_OBJECT_TYPE,
SLOT_LAST_OBJECT_TYPE
)
from knowledgebase.car_knowledgebase import CarKnowledgeBase
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
import logging
logger = logging.getLogger(__name__)


ATTRIBUTE_MAP = {"price":"价格（万）",
            "engine_power_kw":"发动机功率（千瓦）",
            "seat_number":"座位个数",
            "series_level":"类型",
            "drive_name":"驱动方式",
            "liter":"排量"
            }


class ActionAskCarAttribute(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db=MYSQL_DBNAME, user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["level_name"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_car_attribute"


    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:
        """
        Executes this action. If the user ask a question about an attribute,
        the knowledge base is queried for that attribute. Otherwise, if no
        attribute was detected in the request or the user is talking about a new
        object type, multiple objects of the requested type are returned from the
        knowledge base.

        Args:
            dispatcher: the dispatcher
            tracker: the tracker
            domain: the domain

        Returns: list of slots

        """
        logger.info("Enter action: %s", self.name())
        curr_model_id = tracker.get_slot('curr_model')
        mention = tracker.get_slot(SLOT_MENTION)
        logger.info("mention = %s", mention)
        if curr_model_id is None:
            logger.info("model_id is None")
            dispatcher.utter_message(text="抱歉，没有获取到车型ID")
            return [SlotSet(SLOT_MODEL_NAME, None), SlotSet(SLOT_MENTION, None)]

        current_model = await utils.call_potential_coroutine(self.knowledge_base.get_object(curr_model_id))
        current_model = current_model[0]
        logger.info("current model is: %s", current_model['model_name'])
        if current_model is None:
            dispatcher.utter_message(text="抱歉，没有获取到具体车型")
            return [SlotSet(SLOT_MODEL_NAME, None), SlotSet(SLOT_MENTION, None)]
        attributes = tracker.get_slot(SLOT_ATTRIBUTE_LIST)
        logger.info("attributes = %s", attributes)
        if attributes is None or len(attributes) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到车的属性名")
            return [SlotSet(SLOT_MODEL_NAME, None), SlotSet(SLOT_MENTION, None), SlotSet('car', None)]

        for attr in attributes:
            if attr == 'price' and current_model[attr] is None:
                dispatcher.utter_message(text=f"该车目前的指导价是：{current_model['model_price']}万元")
                continue
            if attr == 'model_intr' and current_model[attr] is None:
                curr_series = await utils.call_potential_coroutine(self.knowledge_base.get_series_intr(current_model['series_id']))
                curr_series = curr_series[0]
                logger.info("current series = %s", curr_series)
                dispatcher.utter_message(text=curr_series['series_intr'])
                continue
            if current_model[attr] is None or len(current_model[attr]) == 0:
                dispatcher.utter_message(text="知识点在进一步完善中，敬请期待！")
                continue
            dispatcher.utter_message(text=current_model[attr])
        buttons = []
        b1 = {"title":"是", "payload":"/affirm"}
        b2 = {"title":"否", "payload":"/deny"}
        buttons.append(b1)
        buttons.append(b2)
        dispatcher.utter_message(text="还有什么要了解的吗？", buttons=buttons)
        return [SlotSet(SLOT_LAST_OBJECT_TYPE, "car"),
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_OBJECT_TYPE, "car"),
                SlotSet(SLOT_MODEL_NAME, None),
                SlotSet(SLOT_ATTRIBUTE_LIST, None),
                SlotSet('car', None)]
