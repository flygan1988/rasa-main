from typing import Dict, Text, List
import sys
sys.path.append('../')
from rasa_sdk import Tracker
from rasa_sdk.events import EventType
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action
from rasa_sdk import utils
from utils.constants import (
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_USER,
    MYSQL_DBNAME,
    RECOM_PARAMS,
    RECOM_SLOT_MAP,
    RECOM_UTTER_MAP,
    RECOM_CHI_MAP,
    SLOT_LISTED_OBJECTS,
    SLOT_RECO_HIS
)
from reco.reco_main import reco_car_model

from knowledgebase.car_knowledgebase import CarKnowledgeBase
import logging
import random


logger = logging.getLogger(__name__)

SLOT_LIST = ['fuel_type', 'series_level', 'price', 'space']

class RequestAction(Action):
    def __init__(
        self, use_last_object_mention: bool = True
    ) -> None:
        self.knowledge_base = CarKnowledgeBase(db=MYSQL_DBNAME, user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.knowledge_base.set_representation_function_of_object(
            "car", lambda obj: obj["model_name"] + " (" + obj["level_name"] + ")"
        )
        self.use_last_object_mention = use_last_object_mention


    def name(self) -> Text:
        return "action_request"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        latest_intent = tracker.get_intent_of_latest_message()
        if latest_intent == 'affirm':
            model_id = tracker.get_slot('curr_model')
            curr_model = await utils.call_potential_coroutine(self.knowledge_base.get_object(model_id))
            if curr_model is None or len(curr_model) == 0:
                dispatcher.utter_message(text="抱歉，未获取到当前车型ID")
                slots = [SlotSet(RECOM_SLOT_MAP[slot], None) for slot in RECOM_PARAMS]
                return slots
            curr_model = curr_model[0]
            if curr_model['model_intr'] is not None and len(curr_model['model_intr']) != 0:
                dispatcher.utter_message(text=curr_model['model_intr'])
            else:
                curr_series = await utils.call_potential_coroutine(self.knowledge_base.get_series_intr(curr_model['series_id']))
                curr_series = curr_series[0]
                dispatcher.utter_message(text=curr_series['series_intr'])
            dispatcher.utter_message(response="utter_dealer_detail")
            slots = [SlotSet(RECOM_SLOT_MAP[slot], None) for slot in RECOM_PARAMS]
            return slots + [SlotSet(SLOT_LISTED_OBJECTS, None), SlotSet(SLOT_RECO_HIS, None)]
        elif latest_intent == 'deny':
            listed_objs = tracker.get_slot(SLOT_LISTED_OBJECTS)
            reco_his = tracker.get_slot(SLOT_RECO_HIS)
            if reco_his is None:
                reco_his = {}
            if listed_objs is not None:
                for obj in listed_objs:
                    reco_his[obj['model_id']] = -1

            for slot in SLOT_LIST:
                logger.info(slot+"= %s", tracker.get_slot(slot))
            curr_slot = None
            for slot in SLOT_LIST:
                if tracker.get_slot(slot) is None:
                    curr_slot = slot
                    break
            buttons = []
            if curr_slot == 'series_level':
                b1 = {'title': '轿车', 'payload': '/inform_series_level{"series_level":"轿车"}'}
                b2 = {'title': 'SUV', 'payload': '/inform_series_level{"series_level":"SUV"}'}
                b3 = {'title': 'MPV', 'payload': '/inform_series_level{"series_level":"MPV"}'}
                # b4 = {'title': '跑车', 'payload': '/inform_series_level{"series_level":"跑车"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                # buttons.append(b4)
                dispatcher.utter_message(text="请问您喜欢以下哪种车型？", buttons=buttons)
            elif curr_slot == 'price':
                b1 = {'title': '10万以内', 'payload': '/inform_price{"price":["0", "100000"]}'}
                b2 = {'title': '10万--20万', 'payload': '/inform_price{"price":["100000", "200000"]}'}
                b3 = {'title': '20万--30万', 'payload': '/inform_price{"price":["200000", "300000"]}'}
                b4 = {'title': '30万以上', 'payload': '/inform_price{"price":["300000", "999999"]}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                buttons.append(b4)
                dispatcher.utter_message(text="请问您预算多少？", buttons=buttons)
            elif curr_slot == 'space':
                b1 = {'title': '紧凑型', 'payload': '/inform_space{"space":"紧凑型"}'}
                b2 = {'title': '中型', 'payload': '/inform_space{"space":"中型"}'}
                b3 = {'title': '中大型', 'payload': '/inform_space{"space":"中大型"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                dispatcher.utter_message(text="请问您对车的空间需求是什么？", buttons=buttons)
            elif curr_slot == 'fuel_type':
                b1 = {'title': '新能源', 'payload': '/inform_fuel_type{"fuel_type":"新能源"}'}
                b2 = {'title': '汽油', 'payload': '/inform_fuel_type{"fuel_type":"汽油"}'}
                b3 = {'title': '油电混合', 'payload': '/inform_fuel_type{"fuel_type":"油电混合"}'}
                b4 = {'title': '纯电', 'payload': '/inform_fuel_type{"fuel_type":"纯电"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                buttons.append(b4)
                dispatcher.utter_message(text="请问您喜欢哪种能源类型？", buttons=buttons)
            else:
                dispatcher.utter_message(text="抱歉，我只能帮你到这了")
            if curr_slot is None:
                slots = [SlotSet(RECOM_SLOT_MAP[slot], None) for slot in RECOM_PARAMS]
                return slots + [SlotSet(SLOT_LISTED_OBJECTS, None), SlotSet(SLOT_RECO_HIS, None)]

            return [SlotSet(SLOT_LISTED_OBJECTS, None), SlotSet(SLOT_RECO_HIS, reco_his)]
        else:
            curr_slot = None
            for slot in SLOT_LIST:
                if tracker.get_slot(slot) is None:
                    curr_slot = slot
                    break
            params = {}
            for slot in RECOM_PARAMS:
                value = tracker.get_slot(RECOM_SLOT_MAP[slot])
                if type(value) == list:
                    params[slot] = value
                else:
                    params[slot] = [value] if value is not None else []
            logger.info("recommend params = %s", [params])
            reco_his = tracker.get_slot(SLOT_RECO_HIS)
            reco_his = {} if reco_his is None else reco_his
            logger.info("recommend reco_his = %s", reco_his)
            rmd_rst, rst_dsc, rst_flag = reco_car_model([params], reco_his)
            logger.info("rmd_rst = %s", rmd_rst)
            logger.info("rst_dsc = %s", rst_dsc)
            logger.info("rst_flag = %s", rst_flag)
            res = rmd_rst[0]
            buttons = []
            if (len(res) > 0 and rst_flag[0] == 1) or curr_slot is None:
                ##适合推荐
                for i, reco_model in enumerate(rmd_rst[0]):
                    button = {'title': reco_model['model_name'], 'payload': '/affirm{"curr_model":"'+reco_model['model_id']+'"}'}
                    buttons.append(button)
                b2 = {'title': '无', 'payload': '/deny'}
                tag = rst_dsc[0]['tag']
                dsc = rst_dsc[0]['dsc']
                utter = RECOM_UTTER_MAP[tag]
                tmp_str = ",".join([RECOM_CHI_MAP[p] for p in dsc])
                utter = utter.format(tmp_str)
                buttons.append(b2)
                dispatcher.utter_message(text=utter, buttons=buttons)

                dispatcher.utter_message(text="给您推荐以上车型，请点击感兴趣的车型了解详情或点击<b>'无'</b>按钮继续")
                return [SlotSet(SLOT_LISTED_OBJECTS, res)]
            if curr_slot == 'series_level':
                b1 = {'title': '轿车', 'payload': '/inform_series_level{"series_level":"轿车"}'}
                b2 = {'title': 'SUV', 'payload': '/inform_series_level{"series_level":"SUV"}'}
                b3 = {'title': 'MPV', 'payload': '/inform_series_level{"series_level":"MPV"}'}
                #b4 = {'title': '跑车', 'payload': '/inform_series_level{"series_level":"跑车"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                #buttons.append(b4)
                dispatcher.utter_message(text="请问您喜欢以下哪种车型？", buttons=buttons)
            elif curr_slot == 'price':
                b1 = {'title': '10万以内', 'payload': '/inform_price{"price":["0", "100000"]}'}
                b2 = {'title': '10万--20万', 'payload': '/inform_price{"price":["100000", "200000"]}'}
                b3 = {'title': '20万--30万', 'payload': '/inform_price{"price":["200000", "300000"]}'}
                b4 = {'title': '30万以上', 'payload': '/inform_price{"price":["300000", "999999"]}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                buttons.append(b4)
                dispatcher.utter_message(text="请问您预算多少？", buttons=buttons)
            elif curr_slot == 'space':
                b1 = {'title': '紧凑型', 'payload': '/inform_space{"space":"紧凑型"}'}
                b2 = {'title': '中型', 'payload': '/inform_space{"space":"中型"}'}
                b3 = {'title': '中大型', 'payload': '/inform_space{"space":"中大型"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                dispatcher.utter_message(text="请问您对车的空间需求是什么？", buttons=buttons)
            elif curr_slot == 'fuel_type':
                b1 = {'title': '新能源', 'payload': '/inform_fuel_type{"fuel_type":"新能源"}'}
                b2 = {'title': '汽油', 'payload': '/inform_fuel_type{"fuel_type":"汽油"}'}
                b3 = {'title': '油电混合', 'payload': '/inform_fuel_type{"fuel_type":"油电混合"}'}
                b4 = {'title': '纯电', 'payload': '/inform_fuel_type{"fuel_type":"纯电"}'}
                buttons.append(b1)
                buttons.append(b2)
                buttons.append(b3)
                buttons.append(b4)
                dispatcher.utter_message(text="请问您喜欢哪种能源类型？", buttons=buttons)
            return []

