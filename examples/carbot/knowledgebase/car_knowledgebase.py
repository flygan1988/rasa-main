from rasa_sdk.knowledge_base.storage import KnowledgeBase
import json
import logging
import os
import random
from typing import DefaultDict, Text, Callable, Dict, List, Any, Optional
from collections import defaultdict
from sqlalchemy import create_engine

from rasa_sdk import utils

logger = logging.getLogger(__name__)

class CarKnowledgeBase(KnowledgeBase):
    def __init__(self, db: Text, user: Text, password: Text, host='127.0.0.1', port=3306) -> None:
        """
            加载数据库连接
        """
        self.data_engine = create_engine(str(r"mysql+mysqldb://%s:" + '%s' + "@%s/%s") % (user, password, host, db))
        self.key_attribute = "model_id"
        super().__init__()

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
            key_attribute: the name of the key attribute
        """
        self.key_attribute = key_attribute

    async def get_attributes_of_object(self) -> List[Text]:
        sql = "SELECT * FROM model LIMIT 1"

        res = self.data_engine.execute(sql)
        return res.keys()

    async def get_objects(
        self, object_type: Text, attributes: List[Dict[Text, Text]], limit: int = 5
    ) -> List[Dict[Text, Any]]:
        if object_type not in self.data:
            return []

        objects = self.data[object_type]

        # filter objects by attributes
        if attributes:
            objects = list(
                filter(
                    lambda obj: [
                        obj[a["name"]] == a["value"] for a in attributes
                    ].count(False)
                    == 0,
                    objects,
                )
            )

        random.shuffle(objects)

        return objects[:limit]

    async def get_object(
        self, object_identifier: Text
    ) -> Optional[Dict[Text, Any]]:
        if object_identifier is None:
            return None

        sql = "SELECT * FROM model WHERE model_id = {}".format(object_identifier)

        res = self.data_engine.execute(sql)
        return [dict(zip(res.keys(), result)) for result in res]

if __name__ == '__main__':
    import asyncio
    cardb = CarKnowledgeBase(db='che300', user='root', password='password')
    loop = asyncio.get_event_loop()
    objs = loop.run_until_complete(cardb.get_attributes_of_object())
    for obj in objs:
        print(obj)
