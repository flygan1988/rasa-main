from rasa_sdk.knowledge_base.storage import KnowledgeBase
import logging
import asyncio
from typing import DefaultDict, Text, Callable, Dict, List, Any, Optional
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class CarKnowledgeBase(KnowledgeBase):
    def __init__(self, db: Text, user: Text, password: Text, host='127.0.0.1', port=3306) -> None:
        """
            加载数据库连接
        """
        db_url = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, db)
        self.data_engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)

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
        sql = "SELECT * FROM car300_model LIMIT 1"
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)
        res = [key for key in res.keys()]
        return res

    async def insert_conversation_history(self, sender_id, user_message, bot_response, metadata, create_time):
        """
        Log user conversation history
        """
        sql = """INSERT INTO conversation_history
              VALUES("{0}","{1}","{2}","{3}","{4}")""".format(sender_id,user_message,bot_response,metadata,create_time)
        with self.data_engine.connect() as conn:
            conn.execute(sql)

    async def get_objects_by_series_name(self, series_name: Text):
        sql = """SELECT m.*, s.level_name FROM car300_model m 
                join car300_series s on m.series_id = s.series_id
                where m.model_status = '在售' 
                and m.series_name = '{}'""".format(series_name)
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)
        return [dict(zip(res.keys(), result)) for result in res]

    async def get_object(
        self, object_identifier: Text
    ) -> Optional[Dict[Text, Any]]:
        if object_identifier is None:
            return None

        sql = """SELECT m.series_id, m.model_id, m.model_name, m.price model_price, m.liter, m.gear_type, m.model_year, m.drive_name,
                c.model_intr, c.hdge, c.popularity, c.cost_effective, c.price, c.warranty, c.configuration, c.power, c.engine,
                c.room, c.size, c.battery, c.voyage, c.charging, c.fuel_cost, c.colour, c.exterior, c.audio, c.interior, c.seat,
                c.control_screen, c.hologram, c.steering_wheel, c.smart_system, c.smart_system_update, c.safety
                FROM car300_model m
                LEFT JOIN carkg_model_qa c ON m.model_id = c.model_id
                WHERE m.model_id = '{}'""".format(object_identifier)
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)
        return [dict(zip(res.keys(), result)) for result in res]


    async def get_series_names(self, series_name: Text):
        sql = """SELECT distinct(series_name) FROM car300_model
                where model_status = '在售' 
                and series_name like '%%{}%%'""".format(series_name)
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)

        res = [dict(zip(res.keys(), result)) for result in res]
        return res

    async def get_series_intr(self, series_id: Text):
        sql = """SELECT * FROM carkg_series_intr
                where series_id = '{}'""".format(series_id)
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)

        res = [dict(zip(res.keys(), result)) for result in res]
        return res

    async def get_gear_type_count(self, series_name: Text):
        sql = """SELECT count(distinct gear_type) num FROM car300_model
                where model_status = '在售' 
                and series_name like '%%{}%%'""".format(series_name)
        with self.data_engine.connect() as conn:
            res = conn.execute(sql)

        res = [dict(zip(res.keys(), result)) for result in res]
        return res[0]['num']

if __name__ == '__main__':
    import asyncio
    cardb = CarKnowledgeBase(db='carkb', user='root', password='password', host='10.116.47.86')
    loop = asyncio.get_event_loop()
    objs = loop.run_until_complete(cardb.get_objects_by_series_name('朗逸'))
    print(objs)
    # objs = list(filter(lambda obj: obj['is_green'] == 0, objs))
    # print(len(objs))
    # print(loop.run_until_complete(cardb.get_gear_type_count('朗逸')))
