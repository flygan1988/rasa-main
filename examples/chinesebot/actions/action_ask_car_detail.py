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

attribute_list = ["name",
            "color",
            "type",
            "seat",
            "price-range",
            "power"]
attribute_map = {"name":"车型",
            "color":"颜色",
            "type":"类型",
            "seat":"座位",
            "price-range":"价格",
            "power":"动力参数"}

class ActionAskCarDetail(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = InMemoryKnowledgeBase("knowledge_base_data.json")
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["name"] + " (" + obj["type"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_ask_car_detail"

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

        new_request = object_type != last_object_type

        if not object_type:
            # object type always needs to be set as this is needed to query the
            # knowledge base
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return []

        # if not attribute or new_request:
        #     return await self._query_objects(dispatcher, object_type, tracker)
        # elif attribute:
        #     return await self._query_attribute(
        #         dispatcher, object_type, attribute, tracker
        #     )
        object_name = get_object_name(tracker, self.knowledge_base.ordinal_mention_mapping,
                                      self.use_last_object_mention)
        if not object_name:
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return [SlotSet(SLOT_MENTION, None)]
        object_of_interest = await utils.call_potential_coroutine(
            self.knowledge_base.get_object(object_type, object_name)
        )
        if not object_of_interest:
            dispatcher.utter_message(text="不是很明白您的意思，请再说一次！")
            return [SlotSet(SLOT_MENTION, None)]
        response_list = []
        for attribute in object_of_interest:
            if attribute == "id":
                continue
            resp = f"'{attribute_map[attribute]}'：'{object_of_interest[attribute]}'"
            response_list.append(resp)
        response_text = "\n".join(response_list)

        dispatcher.utter_message(text=response_text)

        key_attribute = await utils.call_potential_coroutine(
            self.knowledge_base.get_key_attribute_of_object(object_type)
        )

        object_identifier = object_of_interest[key_attribute]

        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_ATTRIBUTE, None),
            SlotSet(SLOT_MENTION, None),
            SlotSet(SLOT_LAST_OBJECT, object_identifier),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
        ]

        return slots