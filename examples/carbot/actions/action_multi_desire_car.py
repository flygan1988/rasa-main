from typing import Text, Dict, List, Any

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from rasa_sdk.knowledge_base.utils import (
    SLOT_OBJECT_TYPE,
    SLOT_LAST_OBJECT_TYPE,
    SLOT_ATTRIBUTE,
    reset_attribute_slots,
    SLOT_MENTION,
    SLOT_LAST_OBJECT,
    SLOT_LISTED_OBJECTS,
    get_object_name,
    get_attribute_slots,
)
from rasa_sdk import utils
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from .myknowledgebase import MyKnowledgeBase

attribute_map = {"name":"车型",
            "color":"颜色",
            "category":"类型",
            "seat":"座位",
            "price":"价格",
            "power":"动力参数",
            "usage":"用途"}

class MultiDesireCare(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = MyKnowledgeBase("knowledge_base_data.json")
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["name"] + " (" + obj["category"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_multi_desire_car"

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
        object_type = tracker.get_slot(SLOT_OBJECT_TYPE)
        if object_type is None:
            object_type = "car"
        # last_object_type = tracker.get_slot(SLOT_LAST_OBJECT_TYPE)
        # attributes = [tracker.get_slot(attribute) for attribute in attribute_list if not tracker.get_slot(attribute)]

        # new_request = object_type != last_object_type

        car_list = tracker.get_slot(object_type)
        print(car_list)

        if car_list is None or len(car_list) == 0:
            dispatcher.utter_message(text="抱歉，我没有获取到车名")
            return [SlotSet(object_type, None)]

        key_attribute = await utils.call_potential_coroutine(
            self.knowledge_base.get_key_attribute_of_object(object_type)
        )
        response_list = []
        list_objs = []
        for object_name in car_list:
            object_of_interest = await utils.call_potential_coroutine(
                self.knowledge_base.get_object(object_type, object_name)
            )
            if object_of_interest:
                list_objs.append(object_of_interest[key_attribute])
                for attribute in object_of_interest:
                    if attribute == "id":
                        continue
                    resp = f"'{attribute_map[attribute]}'：'{object_of_interest[attribute]}'"
                    response_list.append(resp)
            response_list.append("*****************************")

        response_text = "\n".join(response_list)

        dispatcher.utter_message(text=response_text)
        dispatcher.utter_message(text="\n")

        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_ATTRIBUTE, None),
            SlotSet(SLOT_MENTION, None),
            SlotSet(
                SLOT_LISTED_OBJECTS, list_objs
            ),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
        ]

        return slots

