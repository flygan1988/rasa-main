from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction

class ValidateNoDesireForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_no_desire_car_form"

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
    def car_series_level_db() -> List[Text]:
        """Database of supported car series_level."""

        return [
            "SUV",
            "MPV",
            "轿车"
        ]

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer."""

        try:
            int(string)
            return True
        except ValueError:
            return False

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
        else:
            return {"is_green": 0}

    def validate_series_level(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car series_level value."""

        if value.upper() in self.car_series_level_db():
            # validation succeeded, set the value of the "gear_type" slot to value
            return {"series_level": value.upper()}
        else:
            dispatcher.utter_message(response="utter_wrong_series_level")
            return {"series_level": None}

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
