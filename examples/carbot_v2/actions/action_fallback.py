from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action

import logging

logger = logging.getLogger(__name__)

import requests
import json

def get_response(message):
    url = "http://api.qingyunke.com/api.php?key=free&appid=0&msg={}".format(message)
    response = requests.get(url)
    res = json.loads(response.text)
    return res

class FallbackAction(Action):

    def name(self) -> Text:
        return "action_fallback"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        logger.info("Enter action: %s", self.name())
        latest_msg = tracker.latest_message.get('text')
        try:
            res = get_response(latest_msg)
            msg = res['content'].replace('{br}','<br>').replace('&quot', '"')
            dispatcher.utter_message(text=msg)
        except:
            dispatcher.utter_message(text="默认处理接口报错")
        return []