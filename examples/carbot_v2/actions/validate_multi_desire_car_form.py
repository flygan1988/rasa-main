from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk import utils
from knowledgebase.car_knowledgebase import CarKnowledgeBase

class ValidateMultiDesireForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_multi_desire_car_form"

    def __init__(self):
        self.knowledge_base = CarKnowledgeBase(db='che300', user='root', password='password')

    @staticmethod
    def car_space_db() -> List[Text]:
        """Database of supported car space."""

        return [
            "小型",
            "紧凑型",
            "中型",
            "中大型",
            "无"
        ]

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
        car_list = tracker.get_slot('car')
        if car_list is None or len(car_list) == 0:
            return []
        additional_slots = []
        suv_list = []
        for series_name in car_list:
            mlist = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name))
            mlist = list(filter(lambda model: "SUV" in model["car_struct"], mlist))
            if len(mlist) > 0:
                suv_list.append(1)
            else:
                suv_list.append(0)
        suv_set = set(suv_list)
        if len(suv_set) > 1:
            additional_slots.append("car_usage")

        return additional_slots + domain_slots

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

    def validate_car_usage(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car usage value."""
        if "上班" in value or "家用" in value or "商务" in value:
            return {"car_usage": "轿车"}
        else:
            return {"car_usage": "SUV"}

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

    def validate_space(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car space value."""
        if value in self.car_space_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"space": value}
        else:
            dispatcher.utter_message(response="utter_wrong_space")
            return {"space": None}

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
