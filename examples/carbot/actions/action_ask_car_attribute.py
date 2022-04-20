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
from rasa_sdk.knowledge_base.storage import KnowledgeBase, InMemoryKnowledgeBase

# attribute_list = ["name",
#             "color",
#             "type",
#             "seat",
#             "price",
#             "power"]
attribute_map = {"name":"车型",
            "color":"颜色",
            "category":"类型",
            "seat":"座位",
            "price":"价格",
            "power":"动力参数",
            "usage":"用途"}


class ActionAskCarAttribute(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = InMemoryKnowledgeBase("knowledge_base_data.json")
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["name"] + " (" + obj["category"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_ask_car_attribute"

    def utter_attribute_value(
        self,
        dispatcher: CollectingDispatcher,
        object_name: Text,
        attribute_name: Text,
        attribute_value: Text,
    ):
        """
        Utters a response that informs the user about the attribute value of the
        attribute of interest.

        Args:
            dispatcher: the dispatcher
            object_name: the name of the object
            attribute_name: the name of the attribute
            attribute_value: the value of the attribute
        """
        if attribute_value:
            dispatcher.utter_message(
                text=f"'{object_name}' 的'{attribute_map[attribute_name]}' 是： '{attribute_value}'."
            )
        else:
            dispatcher.utter_message(
                text=f"没找到相关信息，试试换一种说法。"
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
        last_object_type = tracker.get_slot(SLOT_LAST_OBJECT_TYPE)
        # attributes = [tracker.get_slot(attribute) for attribute in attribute_list if not tracker.get_slot(attribute)]
        attribute = tracker.get_slot(SLOT_ATTRIBUTE)
        print(attribute)
        new_request = object_type != last_object_type

        if not object_type:
            # object type always needs to be set as this is needed to query the
            # knowledge base
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return []

        if not attribute or new_request:
            return await self._query_objects(dispatcher, object_type, tracker)
        elif attribute:
            return await self._query_attribute(
                dispatcher, object_type, attribute, tracker
            )
        # if len(attributes) != 0:
        #     return await self._query_attributes(dispatcher, object_type, attributes, tracker)

        dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
        return []

    async def _query_attribute(
        self,
        dispatcher: CollectingDispatcher,
        object_type: Text,
        attribute: Text,
        tracker: Tracker,
    ) -> List[Dict]:
        """
        Queries the knowledge base for the value of the requested attribute of the
        mentioned object and outputs it to the user.

        Args:
            dispatcher: the dispatcher
            tracker: the tracker

        Returns: list of slots
        """
        object_name = get_object_name(
            tracker,
            self.knowledge_base.ordinal_mention_mapping,
            self.use_last_object_mention,
        )
        print(object_name)
        if not object_name or not attribute:
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return [SlotSet(SLOT_MENTION, None)]

        object_of_interest = await utils.call_potential_coroutine(
            self.knowledge_base.get_object(object_type, object_name)
        )
        print(object_of_interest)

        if not object_of_interest or attribute not in object_of_interest:
            print("*********")
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return [SlotSet(SLOT_MENTION, None)]

        value = object_of_interest[attribute]

        object_repr_func = await utils.call_potential_coroutine(
            self.knowledge_base.get_representation_function_of_object(object_type)
        )

        object_representation = object_repr_func(object_of_interest)

        key_attribute = await utils.call_potential_coroutine(
            self.knowledge_base.get_key_attribute_of_object(object_type)
        )

        object_identifier = object_of_interest[key_attribute]

        await utils.call_potential_coroutine(
            self.utter_attribute_value(
                dispatcher, object_representation, attribute, value
            )
        )

        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_ATTRIBUTE, None),
            SlotSet(SLOT_MENTION, None),
            SlotSet(SLOT_LAST_OBJECT, object_identifier),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
        ]

        return slots