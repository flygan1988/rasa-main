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

class ActionRecomCarPrice(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = MyKnowledgeBase("knowledge_base_data.json")
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["name"] + " (" + obj["category"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_recomm_car_by_price"

    async def utter_objects(
        self,
        dispatcher: CollectingDispatcher,
        object_type: Text,
        objects: List[Dict[Text, Any]],
    ):
        """
        Utters a response to the user that lists all found objects.

        Args:
            dispatcher: the dispatcher
            object_type: the object type
            objects: the list of objects
        """
        if objects:
            dispatcher.utter_message(
                text=f"推荐一下几款车型供参考:"
            )

            repr_function = await utils.call_potential_coroutine(
                self.knowledge_base.get_representation_function_of_object(object_type)
            )

            for i, obj in enumerate(objects, 1):
                dispatcher.utter_message(text=f"{i}: {repr_function(obj)}")
        else:
            dispatcher.utter_message(
                text=f"I could not find any objects of type '{object_type}'."
            )

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

        last_object_id = tracker.get_slot(SLOT_LAST_OBJECT)
        if last_object_id is None:
            dispatcher.utter_message(text="抱歉，我没有获取到您提到的车子")
            return []

        object_of_interest = await utils.call_potential_coroutine(
            self.knowledge_base.get_object(object_type, last_object_id)
        )

        price_range = object_of_interest["price"].split("-")
        all_objs = await utils.call_potential_coroutine(
            self.knowledge_base.get_objects(object_type, None)
        )
        recomm_objs = []
        for obj in all_objs:
            if obj["id"] == object_of_interest["id"]:
                continue
            obj_price_range = obj["price"].split("-")
            if (int(price_range[0]) >= int(obj_price_range[0]) and int(price_range[0]) <= int(obj_price_range[1])) or (int(price_range[1]) >= int(obj_price_range[0]) and int(price_range[1]) <= int(obj_price_range[1])):
                recomm_objs.append(obj)

        await utils.call_potential_coroutine(
            self.utter_objects(dispatcher, object_type, recomm_objs)
        )

        key_attribute = await utils.call_potential_coroutine(
            self.knowledge_base.get_key_attribute_of_object(object_type)
        )

        last_object = None if len(recomm_objs) > 1 else recomm_objs[0][key_attribute]

        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_MENTION, None),
            SlotSet(SLOT_ATTRIBUTE, None),
            SlotSet(SLOT_LAST_OBJECT, last_object),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
            SlotSet(
                SLOT_LISTED_OBJECTS, list(map(lambda e: e[key_attribute], recomm_objs))
            ),
        ]

        return slots
