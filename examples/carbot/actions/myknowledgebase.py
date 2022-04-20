from rasa_sdk.knowledge_base.storage import KnowledgeBase
import json
import logging
import os
import random
from typing import DefaultDict, Text, Callable, Dict, List, Any, Optional

from rasa_sdk import utils

logger = logging.getLogger(__name__)

class MyKnowledgeBase(KnowledgeBase):
    def __init__(self, data_file: Text) -> None:
        """
        Initialize the in-memory knowledge base.
        Loads the data from the given data file into memory.

        Args:
            data_file: the path to the file containing the data
        """
        self.data_file = data_file
        self.data: Dict[Text, Any] = {}
        self.load()
        super().__init__()

    def load(self) -> None:
        """
        Load the data from the given file and initialize an in-memory knowledge base.
        """
        try:
            with open(self.data_file, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            raise ValueError(f"File '{self.data_file}' does not exist.")

        try:
            self.data = json.loads(content)
        except ValueError as e:
            raise ValueError(
                f"Failed to read json from '{os.path.abspath(self.data_file)}'. Error: {e}"
            )

    def set_representation_function_of_object(
        self, object_type: Text, representation_function: Callable
    ) -> None:
        """
        Set the representation function of the given object type.

        Args:
            object_type: the object type
            representation_function: the representation function
        """
        self.representation_function[object_type] = representation_function

    def set_key_attribute_of_object(
        self, object_type: Text, key_attribute: Text
    ) -> None:
        """
        Set the key attribute of the given object type.

        Args:
            object_type: the object type
            key_attribute: the name of the key attribute
        """
        self.key_attribute[object_type] = key_attribute

    async def get_attributes_of_object(self, object_type: Text) -> List[Text]:
        if object_type not in self.data or not self.data[object_type]:
            return []

        first_object = self.data[object_type][0]

        return list(first_object.keys())


    async def get_objects(
        self, object_type: Text, attributes: List[Dict[Text, Text]], limit: int = 5
    ) -> List[Dict[Text, Any]]:
        if object_type not in self.data:
            return []

        objects = self.data[object_type]
        if attributes is None:
            return objects

        # filter objects by attributes
        def if_the_one(obj, attributes):
            for a in attributes:
                if a["name"] != "price" and a["value"] not in obj[a["name"]]:
                    return False
                if a["name"] == "price":
                    price = int(a["value"])
                    price_range = obj[a["name"]].split("-")
                    print(price_range)
                    if price < int(price_range[0]) or price > int(price_range[1]):
                        return False
            return True

        recomm_objs = []
        for obj in objects:
            if if_the_one(obj, attributes):
                recomm_objs.append(obj)

        random.shuffle(recomm_objs)

        return recomm_objs[:limit]

    async def get_object(
        self, object_type: Text, object_identifier: Text
    ) -> Optional[Dict[Text, Any]]:
        if object_type not in self.data:
            return None

        objects = self.data[object_type]

        key_attribute = await utils.call_potential_coroutine(
            self.get_key_attribute_of_object(object_type)
        )

        # filter the objects by its key attribute, for example, 'id'
        objects_of_interest = list(
            filter(
                lambda obj: str(obj[key_attribute]).lower()
                == str(object_identifier).lower(),
                objects,
            )
        )

        # if the object was referred to directly, we need to compare the representation
        # of each object with the given object identifier
        if not objects_of_interest:
            repr_function = await utils.call_potential_coroutine(
                self.get_representation_function_of_object(object_type)
            )

            objects_of_interest = list(
                filter(
                    lambda obj: str(object_identifier).lower()
                    in str(repr_function(obj)).lower(),
                    objects,
                )
            )

        if not objects_of_interest or len(objects_of_interest) > 1:
            # TODO:
            #  if multiple objects are found, the objects could be shown
            #  to the user. the user then needs to clarify what object he meant.
            return None

        return objects_of_interest[0]