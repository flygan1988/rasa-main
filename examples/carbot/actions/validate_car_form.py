from typing import Dict, Text, Any, List, Union

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction

class ValidateCarForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_car_form"

    @staticmethod
    def car_category_db() -> List[Text]:
        """Database of supported car category."""

        return [
            "SUV",
            "轿车"
        ]

    @staticmethod
    def car_usage_db() -> List[Text]:
        """Database of supported car usage."""

        return [
            "家用",
            "商用",
            "越野"
        ]

    @staticmethod
    def is_int(string: Text) -> bool:
        """Check if a string is an integer."""

        try:
            int(string)
            return True
        except ValueError:
            return False

    def validate_category(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car category value."""

        if value.upper() in self.car_category_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"category": value}
        else:
            dispatcher.utter_message(response="utter_wrong_category")
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"category": None}

    def validate_price(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car price range value."""

        if self.is_int(value) and int(value) > 0:
            return {"price": value}
        else:
            dispatcher.utter_message(response="utter_wrong_price")
            # validation failed, set slot to None
            return {"price": None}

    def validate_usage(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate car usage value."""

        if value in self.car_usage_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"usage": value}
        else:
            dispatcher.utter_message(response="utter_wrong_usage")
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"usage": None}
