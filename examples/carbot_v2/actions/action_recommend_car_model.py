from typing import Text, Dict, List, Any

from rasa_sdk import Action
from rasa_sdk import utils
from rasa_sdk.events import SlotSet
from knowledgebase.utils import (
    SLOT_OBJECT_TYPE,
    SLOT_LAST_OBJECT_TYPE,
    SLOT_ATTRIBUTE_LIST,
    SLOT_LAST_MODEL,
    SLOT_LISTED_MODELS,
    SLOT_MODEL_NAME,
    reset_attribute_slots,
    SLOT_MENTION,
    SLOT_LAST_OBJECT,
    SLOT_LISTED_OBJECTS,
    get_object,
    get_attribute_slots,
    get_car_model_by_closed_price
)
from knowledgebase.car_knowledgebase import CarKnowledgeBase
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
import logging
logger = logging.getLogger(__name__)

ONE_DESIRE_CAR_SLOTS = {"price":None, "engine_power_kw":None, "gear_type":None, "model_level":None, "is_green":None}
NO_DESIRE_CAR_SLOTS = {"series_level":None, "engine_power_kw":None, "price":None, "space":None, "is_green":None}
MULTI_DESIRE_CAR_SLOTS = {"engine_power_kw":None, "price":None, "space":None, "gear_type":None, "car_usage":None}

class ActionRecommCarModel(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db='che300', user='root', password='password')
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: "{}(价格:{}万, 发动机动力:{}千瓦, 变速器类型:{}, 类型:{})".format(obj["model_name"], obj["price"], obj["engine_power_kw"], obj["gear_type"], obj["series_level"])
        )

        self.use_last_object_mention = use_last_object_mention

    def name(self) -> Text:
        return "action_recommend_car_model"

    def set_slots(self, tracker, object_type, last_model, keys):
        slots = [
            SlotSet(SLOT_OBJECT_TYPE, object_type),
            SlotSet(SLOT_MENTION, None),
            SlotSet(object_type, None),
            SlotSet(SLOT_LAST_OBJECT_TYPE, object_type),
            SlotSet(SLOT_LAST_MODEL, last_model)
        ]
        object_attributes = [attr for attr in keys]
        return slots + reset_attribute_slots(tracker, object_attributes)

    async def utter_objects(
        self,
        tracker: Tracker,
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
                text=f"推荐以下车型供参考:"
            )

            repr_function = await utils.call_potential_coroutine(
                self.knowledge_base.get_representation_function_of_object(object_type)
            )

            for i, obj in enumerate(objects, 1):
                dispatcher.utter_message(text=f"{i}: {repr_function(obj)}")
        else:
            dispatcher.utter_message(
                text="无符合条件的理想车型供选择"
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
        logger.info("Enter action: %s", self.name())
        latest_action_name = tracker.latest_action_name
        if latest_action_name == "one_desire_car_form":
            return await self._query_objects_one_deire_car(dispatcher, tracker)
        elif latest_action_name == "no_desire_car_form":
            return await self._query_objects_no_deire_car(dispatcher, tracker)
        elif latest_action_name == "multi_desire_car_form":
            return await self._query_objects_multi_deire_car(dispatcher, tracker)
        else:
            dispatcher.utter_message(text="暂未实现功能")
            return []

    async def _query_objects_one_deire_car(
        self, dispatcher: CollectingDispatcher, tracker: Tracker
    ) -> List[Dict]:
        """
        Queries the knowledge base for objects of the requested object type and
        outputs those to the user. The objects are filtered by any attribute the
        user mentioned in the request.

        Args:
            dispatcher: the dispatcher
            tracker: the tracker

        Returns: list of slots
        """
        object_type = tracker.get_slot(SLOT_OBJECT_TYPE)
        if object_type is None:
            object_type = "car"
            tracker.add_slots([SlotSet(SLOT_OBJECT_TYPE, object_type)])
        last_model = None
        series_list = tracker.get_slot(object_type)
        logger.info("series_list = %s", series_list)
        if series_list is None or len(series_list) > 1:
            dispatcher.utter_message(text="请提供一个具体车系\n如：帕萨特，途观...之类的车系名称")
            return self.set_slots(tracker, object_type, ONE_DESIRE_CAR_SLOTS.keys())
        series_name = series_list[0]
        car_models = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name))
        if car_models is None or len(car_models) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到车型数据")
            return self.set_slots(tracker, object_type, last_model, ONE_DESIRE_CAR_SLOTS.keys())
        ##get one_desire_car_form slots value
        for slot in ONE_DESIRE_CAR_SLOTS:
            ONE_DESIRE_CAR_SLOTS[slot] = tracker.get_slot(slot)
        logger.info("ONE_DESIRE_CAR_SLOTS = %s", ONE_DESIRE_CAR_SLOTS)

        is_green = ONE_DESIRE_CAR_SLOTS["is_green"]
        ##filter by is_green
        if is_green is not None:
            car_models = list(filter(lambda obj: obj['is_green'] == is_green, car_models))

        gear_type = ONE_DESIRE_CAR_SLOTS['gear_type']
        ##filter by gear_type
        if gear_type is not None and "|" not in gear_type:
            car_models = list(filter(lambda obj: obj['gear_type'] == gear_type, car_models))

        model_level = ONE_DESIRE_CAR_SLOTS["model_level"]
        if model_level != "无":
            car_models.sort(key=lambda model: model['price'])
            if model_level == "高":
                last_model = car_models[-1]
                await utils.call_potential_coroutine(
                    self.utter_objects(tracker, dispatcher, object_type, car_models[-1:])
                )
            elif model_level == "中":
                index = len(car_models) // 2
                last_model = car_models[index]
                await utils.call_potential_coroutine(
                    self.utter_objects(tracker, dispatcher, object_type, car_models[index:index+1])
                )
            else:
                last_model = car_models[0]
                await utils.call_potential_coroutine(
                    self.utter_objects(tracker, dispatcher, object_type, car_models[0:1])
                )
            return self.set_slots(tracker, object_type, last_model, ONE_DESIRE_CAR_SLOTS.keys())

        ##filter by closed price
        price = ONE_DESIRE_CAR_SLOTS['price']
        car_models = get_car_model_by_closed_price(car_models, price, 3)
        ##filter by engine power
        engine_power_kw = ONE_DESIRE_CAR_SLOTS['engine_power_kw']
        car_models.sort(key=lambda model: model['engine_power_kw'])
        if len(car_models) < 3:
            last_model = car_models[0] if len(car_models) == 1 else None
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models)
            )
            return self.set_slots(tracker, object_type, last_model, ONE_DESIRE_CAR_SLOTS.keys())
        if engine_power_kw == "大":
            last_model = car_models[-1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[-1:])
            )
        elif engine_power_kw == "小":
            last_model = car_models[0]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[0:1])
            )
        else:
            last_model = car_models[1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[1:2])
            )

        return self.set_slots(tracker, object_type, last_model, ONE_DESIRE_CAR_SLOTS.keys())

    async def _query_objects_multi_deire_car(
        self, dispatcher: CollectingDispatcher, tracker: Tracker
    ) -> List[Dict]:
        """
        Queries the knowledge base for objects of the requested object type and
        outputs those to the user. The objects are filtered by any attribute the
        user mentioned in the request.

        Args:
            dispatcher: the dispatcher
            tracker: the tracker

        Returns: list of slots
        """
        object_type = tracker.get_slot(SLOT_OBJECT_TYPE)
        if object_type is None:
            object_type = "car"
            tracker.add_slots([SlotSet(SLOT_OBJECT_TYPE, object_type)])
        last_model = None
        series_list = tracker.get_slot(object_type)
        logger.info("series_list = %s", series_list)
        if series_list is None:
            dispatcher.utter_message(text="请提供具体车系名\n如：帕萨特，途观...之类的车系名称")
            return self.set_slots(tracker, object_type, MULTI_DESIRE_CAR_SLOTS.keys())
        car_models = []
        for series_name in series_list:
            car_models.extend(await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_series_name(series_name)))
        if car_models is None or len(car_models) == 0:
            dispatcher.utter_message(text="抱歉，没有获取到车型数据")
            return self.set_slots(tracker, object_type, last_model, MULTI_DESIRE_CAR_SLOTS.keys())
        ##get multi_desire_car_form slots value
        for slot in MULTI_DESIRE_CAR_SLOTS:
            MULTI_DESIRE_CAR_SLOTS[slot] = tracker.get_slot(slot)
        logger.info("MULTI_DESIRE_CAR_SLOTS = %s", MULTI_DESIRE_CAR_SLOTS)
        ##filter by car_usage
        car_usage = MULTI_DESIRE_CAR_SLOTS['car_usage']
        if car_usage == "SUV":
            car_models = list(filter(lambda obj: "SUV" in obj['car_struct'], car_models))
        elif car_usage == "轿车":
            car_models = list(filter(lambda obj: "SUV" not in obj['car_struct'], car_models))

        ##filter by gear_type
        gear_type = MULTI_DESIRE_CAR_SLOTS['gear_type']
        if "|" not in gear_type:
            car_models = list(filter(lambda obj: obj['gear_type'] == gear_type, car_models))
        ##filter by space
        space = MULTI_DESIRE_CAR_SLOTS['space']
        if space != '无':
            car_models = list(filter(lambda obj: space in obj['series_level'], car_models))
        ##filter by closed price
        price = MULTI_DESIRE_CAR_SLOTS['price']
        car_models = get_car_model_by_closed_price(car_models, price, 3)
        ##filter by engine power
        engine_power_kw = MULTI_DESIRE_CAR_SLOTS['engine_power_kw']
        car_models.sort(key=lambda model: model['engine_power_kw'])
        if len(car_models) < 3:
            last_model = car_models[0] if len(car_models) == 1 else None
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models)
            )
            return self.set_slots(tracker, object_type, last_model, MULTI_DESIRE_CAR_SLOTS.keys())
        if engine_power_kw == "大":
            last_model = car_models[-1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[-1:])
            )
        elif engine_power_kw == "小":
            last_model = car_models[0]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[0:1])
            )
        else:
            last_model = car_models[1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[1:2])
            )

        return self.set_slots(tracker, object_type, last_model, MULTI_DESIRE_CAR_SLOTS.keys())

    async def _query_objects_no_deire_car(
        self, dispatcher: CollectingDispatcher, tracker: Tracker
    ) -> List[Dict]:
        """
        Queries the knowledge base for objects of the requested object type and
        outputs those to the user. The objects are filtered by any attribute the
        user mentioned in the request.

        Args:
            dispatcher: the dispatcher
            tracker: the tracker

        Returns: list of slots
        """
        object_type = tracker.get_slot(SLOT_OBJECT_TYPE)
        if object_type is None:
            object_type = "car"
            tracker.add_slots([SlotSet(SLOT_OBJECT_TYPE, object_type)])
        last_model = None
        ##get no_desire_car_form slots value
        for slot in NO_DESIRE_CAR_SLOTS:
            NO_DESIRE_CAR_SLOTS[slot] = tracker.get_slot(slot)
        logger.info("NO_DESIRE_CAR_SLOTS = %s", NO_DESIRE_CAR_SLOTS)

        series_level = NO_DESIRE_CAR_SLOTS['series_level']
        space = NO_DESIRE_CAR_SLOTS['space']
        is_green = NO_DESIRE_CAR_SLOTS['is_green']
        car_models = await utils.call_potential_coroutine(self.knowledge_base.get_objects_by_is_green(is_green))
        if series_level != '轿车':
            car_models = list(filter(lambda obj: series_level in obj['series_level'], car_models))
        else:
            car_models = list(filter(lambda obj: "SUV" not in obj['series_level'] and "MPV" not in obj['series_level'], car_models))
        if space != '无':
            car_models = list(filter(lambda obj: space in obj['series_level'], car_models))

        ##filter by closed price
        price = NO_DESIRE_CAR_SLOTS['price']
        car_models = get_car_model_by_closed_price(car_models, price, 3)
        ##filter by engine power
        engine_power_kw = NO_DESIRE_CAR_SLOTS['engine_power_kw']
        car_models.sort(key=lambda model: model['engine_power_kw'])
        if len(car_models) < 3:
            last_model = car_models[0] if len(car_models) == 1 else None
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models)
            )
            return self.set_slots(tracker, object_type, last_model, NO_DESIRE_CAR_SLOTS.keys())
        if engine_power_kw == "大":
            last_model = car_models[-1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[-1:])
            )
        elif engine_power_kw == "小":
            last_model = car_models[0]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[0:1])
            )
        else:
            last_model = car_models[1]
            await utils.call_potential_coroutine(
                self.utter_objects(tracker, dispatcher, object_type, car_models[1:2])
            )

        return self.set_slots(tracker, object_type, last_model, NO_DESIRE_CAR_SLOTS.keys())