from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk import utils
from knowledgebase.car_knowledgebase import CarKnowledgeBase

class ValidateOneDesireForm(FormValidationAction):

    def __init__(self):
        self.knowledge_base = CarKnowledgeBase(db='che300', user='root', password='password')

    def name(self) -> Text:
        return "validate_one_desire_car_form"

    @staticmethod
    def car_gear_type_db() -> List[Text]:
        """Database of supported car gear type."""

        return [
            "手动",
            "自动"
        ]

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer."""

        try:
            int(string)
            return True
        except ValueError:
            return False

    async def required_slots(
            self,
            domain_slots: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[Text]:
        updated_slots = domain_slots.copy()
        car_list = tracker.get_slot('car')
        if car_list is None or len(car_list) == 0:
            return []
        series_name = car_list[0]
        green_type_count = await utils.call_potential_coroutine(self.knowledge_base.get_green_type_count(series_name))
        if green_type_count <= 1:
            # If the car doesn't have a green energy model, no need to ask
            updated_slots.remove("is_green")
        gear_type_count = await utils.call_potential_coroutine(self.knowledge_base.get_gear_type_count(series_name))
        if gear_type_count <= 1:
            updated_slots.remove("gear_type")
        model_level = tracker.get_slot('model_level')
        if model_level and model_level != '无':
            updated_slots.remove("price")
            updated_slots.remove("engine_power_kw")
        return updated_slots

    def validate_model_level(
            self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if "高" in value or "好" in value:
            return {"model_level": "高"}
        elif "中" in value or "一般" in value or "普通" in value:
            return {"model_level": "中"}
        elif "低" in value or "差" in value:
            return {"model_level": "低"}
        else:
            return {"model_level": "无"}

    def validate_is_green(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car is_green value."""
        if value == "是":
            # validation succeeded, set the value of the "gear_type" slot to value
            return {"is_green": 1}
        elif value == "否":
            return {"is_green": 0}
        else:
            dispatcher.utter_message(response="utter_wrong_is_green")
            return {"is_green": None}

    def validate_gear_type(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car gear type value."""
        if value in self.car_gear_type_db():
            # validation succeeded, set the value of the "gear_type" slot to value
            return {"gear_type": value}
        elif "自动" in value:
            return {"gear_type": "自动"}
        elif "手动" in value:
            return {"gear_type": "手动"}
        elif "都行" in value or "随便" in value or "无" in value or "都可以" in value:
            return {"gear_type": "手动|自动"}
        else:
            dispatcher.utter_message(response="utter_wrong_gear_type")
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"gear_type": None}

    def validate_price(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car price range value."""
        if self.is_int(value) and int(value) > 0:
            return {"price": int(value)}
        else:
            dispatcher.utter_message(response="utter_wrong_price")
            # validation failed, set slot to None
            return {"price": None}

    def validate_engine_power_kw(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car engine_power value."""
        if '大' in value or '好' in value:
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"engine_power_kw": "大"}
        elif '中' in value or '一般' in value:
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"engine_power_kw": "中"}
        else:
            return {"engine_power_kw": "小"}
