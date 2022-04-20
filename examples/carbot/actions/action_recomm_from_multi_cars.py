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

class ActionRecomFromMultiCars(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = MyKnowledgeBase("knowledge_base_data.json")
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["name"] + " (" + obj["category"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_recomm_from_multi_cars"

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

        list_objs = tracker.get_slot(SLOT_LISTED_OBJECTS)
        if list_objs is None or len(list_objs) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到你的意向车子")
            return [SlotSet("usage", None)]

        all_objs = await utils.call_potential_coroutine(
            self.knowledge_base.get_objects(object_type, None)
        )
        all_objs = list(filter(
            lambda obj: obj["id"] in list_objs, all_objs
        ))

        car_usage = tracker.get_slot("usage")
        all_objs = list(filter(
            lambda obj: car_usage in obj["usage"], all_objs
        ))
        sorted(all_objs, key=lambda obj:obj["price"])
        recomm_obj = all_objs[0]
        repr_function = await utils.call_potential_coroutine(
            self.knowledge_base.get_representation_function_of_object(object_type)
        )

        dispatcher.utter_message(text="我觉得适合您的车是：")
        dispatcher.utter_message(text=repr_function(recomm_obj))


        key_attribute = await utils.call_potential_coroutine(
            self.knowledge_base.get_key_attribute_of_object(object_type)
        )

        last_object = recomm_obj[key_attribute]

        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_MENTION, None),
            SlotSet(SLOT_ATTRIBUTE, None),
            SlotSet(SLOT_LAST_OBJECT, last_object),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
            SlotSet(SLOT_LISTED_OBJECTS, None),
            SlotSet("usage", None)
        ]

        return slots
