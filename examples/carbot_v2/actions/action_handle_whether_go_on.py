from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action
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
import logging

logger = logging.getLogger(__name__)

import requests
import json

def get_url(message):
    url = "http://api.qingyunke.com/api.php?key=free&appid=0&msg={}".format(message)
    response = requests.get(url)
    res = json.loads(response.text)
    return res

class AskForModelNameAction(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db=MYSQL_DBNAME, user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_handle_whether_go_on"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        logger.info("Enter action: %s", self.name())
        latest_intent = tracker.get_intent_of_latest_message()
        if latest_intent == 'affirm':
            dispatcher.utter_message(response='utter_ask_more')
        else:
            dispatcher.utter_message(response='utter_dealer_detail')

        return [SlotSet(SLOT_MENTION, None), SlotSet(SLOT_MODEL_NAME, None)]