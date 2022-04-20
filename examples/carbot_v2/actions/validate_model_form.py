from typing import Dict, Text, Any, List

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from knowledgebase.utils import SLOT_LAST_MODEL

class ValidateModelForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_model_form"

    # async def required_slots(
    #         self,
    #         domain_slots: List[Text],
    #         dispatcher: "CollectingDispatcher",
    #         tracker: "Tracker",
    #         domain: "DomainDict",
    # ) -> List[Text]:
    #     update_slots = domain_slots.copy()
    #     print("enter required_slots")
    #     last_model = tracker.get_slot(SLOT_LAST_MODEL)
    #     if last_model is not None:
    #         print("last model is not none")
    #         update_slots.remove("model_name")
    #     return update_slots

    def validate_model_name(
            self, value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        # last_model = tracker.get_slot(SLOT_LAST_MODEL)
        # if last_model is not None:
        #     return {"model_name": last_model["model_name"]}
        return {"model_name": value}
