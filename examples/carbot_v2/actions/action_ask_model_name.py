from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action
from rasa_sdk import utils
from knowledgebase.utils import (
    SLOT_OBJECT_TYPE,
    SLOT_LAST_OBJECT_TYPE,
    SLOT_ATTRIBUTE_LIST,
    reset_attribute_slots,
    SLOT_MENTION,
    SLOT_LAST_OBJECT,
    SLOT_LAST_MODEL,
    SLOT_LISTED_OBJECTS,
    get_object,
    get_attribute_slots,
)

from knowledgebase.car_knowledgebase import CarKnowledgeBase
import logging

logger = logging.getLogger(__name__)


class AskForModelNameAction(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db='che300', user='root', password='password')
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["series_level"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_ask_model_name"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        logger.info("Enter action: action_ask_model_name")
        object_type = tracker.get_slot(SLOT_OBJECT_TYPE)
        if object_type is None:
            object_type = "car"
            tracker.add_slots([SlotSet(SLOT_OBJECT_TYPE, object_type)])

        # last_model = tracker.get_slot(SLOT_LAST_MODEL)
        # if last_model is not None:
        #     logger.info("Use last model as the current mentioned car")
        #     return [SlotSet("model_name", last_model["model_name"])]

        series_list = tracker.get_slot(object_type)
        logger.info("series_list = %s", series_list)

        if series_list is None or len(series_list) > 1:
            dispatcher.utter_message(text="???????????????????????????\n????????????????????????...?????????????????????")
            return []
        series_name = series_list[0]
        objs = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name))
        if objs is None or len(objs) == 0:
            dispatcher.utter_message(text="????????????????????????????????????")
            return []

        for obj in objs:
            dispatcher.utter_message(text=obj['model_name'])

        dispatcher.utter_message(text=f"?????????{series_name}??????????????????????????????????????????????????????????????????\n????????????????????????????????????...")
        return [SlotSet("knowledge_base_listed_models", objs)]