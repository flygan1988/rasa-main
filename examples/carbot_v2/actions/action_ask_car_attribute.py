from typing import Text, Dict, List, Any
import sys
sys.path.append("..")
from rasa_sdk import Action
from rasa_sdk import utils
from rasa_sdk.events import SlotSet
from knowledgebase.utils import (
    SLOT_OBJECT_TYPE,
    SLOT_LAST_OBJECT_TYPE,
    SLOT_ATTRIBUTE_LIST,
    SLOT_LAST_MODEL,
    SLOT_LISTED_MODELS,
    SLOT_MODEL_NAME,
    reset_attribute_slots,
    SLOT_MENTION,
    SLOT_LAST_OBJECT,
    SLOT_LISTED_OBJECTS,
    get_object,
    get_attribute_slots,
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
        self.knowledge_base = CarKnowledgeBase(db='che300', user='root', password='password')
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["series_level"] + ")"
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
        listed_models = tracker.get_slot(SLOT_LISTED_MODELS)
        print(tracker.get_slot("car"))
        if listed_models is None:
            car_list = tracker.get_slot("car")
            if car_list is not None and len(car_list) != 0:
                series_name = car_list[0]
                listed_models = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name))
                tracker.add_slots([SlotSet(SLOT_LISTED_MODELS, listed_models)])

        model_name = tracker.get_slot("model_name")
        print(model_name)

        object = get_object(tracker, self.knowledge_base.ordinal_mention_mapping, "model", self.use_last_object_mention)
        logger.info("object = %s", object)
        if object is None:
            dispatcher.utter_message(text="抱歉，没有获取到具体车型")
            return [SlotSet(SLOT_LISTED_MODELS, None), SlotSet(SLOT_MODEL_NAME, None)]
        attributes = tracker.get_slot(SLOT_ATTRIBUTE_LIST)
        logger.info("attributes = %s", attributes)
        if attributes is None or len(attributes) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到车的属性名")
            return [SlotSet(SLOT_LISTED_MODELS, None)]
        if type(object) != list:
            object = [object]

        for obj in object:
            for attr in attributes:
                message = f"{obj['model_name']}的{ATTRIBUTE_MAP[attr]}：{obj[attr]}"
                dispatcher.utter_message(text=message)
        slot_list = []
        if len(object) == 1:
            slot_list.append(SlotSet(SLOT_LAST_MODEL, object[0]))
        return [SlotSet(SLOT_LAST_OBJECT_TYPE, "car"),
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_OBJECT_TYPE, "car"),
                SlotSet(SLOT_MODEL_NAME, None),
                SlotSet("car", None)] + slot_list
