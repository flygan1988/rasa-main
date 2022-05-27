# -*- coding:utf-8 -*-
# 推荐模块入口
import traceback

from reco import reco_pretreatment, reco_db
import os
import configparser
import datetime


def get_config():
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_path, 'config/config.ini')
    conf_info = configparser.ConfigParser()
    conf_info.read(config_file, encoding="utf-8")
    return conf_info


def reco_car_model(car_int: list, reco_his: dict = None) -> tuple:
    """
    这是车型推荐的主函数，用于与对话系统对接

    入参举例：
        car_int = [{
                “car_series”:[”朗逸“]，
                “version”:[“风尚版”]，
                “year”:[2022]，
                “liter”: [“1.4T”],
                ”gear_type”:[”手动”],
                ”body_type”:[“SUV”],
                ”model_price”:[10000,100000],
                “model_space”:[“紧凑型”],
                ”fuel_type”:[“纯电”],
                “max_miles“:[300],
                ”seat_number”:[7],
                ”favor”:[“性价比高”,”最好看的”]
            }],
        reco_his = {“1743029”:1,}
    出参举例：
        (
        [[{“model_id“:“12345“,“model_name“:“朗逸2022款1.5L自动风尚版“},],],
        [{“tag“:0, “dsc“:[“car_series“,“model_price“,]},],
        [0,]
        )
    具体参考手册
    """
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    # 获取重要度列表
    rmd_rst = []
    rst_dsc = []
    rst_flag = []
    conf_info = get_config()
    car_para_dict = eval(conf_info.get('car_para', 'para_dict'))
    cut_num = eval(conf_info.get('query', 'cut_num'))
    max_result_for_start_reco = eval(conf_info.get('query', 'max_result_for_start_reco'))
    max_input_for_start_reco = eval(conf_info.get('query', 'max_input_for_start_reco'))

    for car_para in car_int:
        standardize_car_int = {}
        result_id_list = []
        result_name_list = []
        result_list = []
        result_tag = -1
        result_tag_dict = {}
        require_acc_list = []
        result_flag = 0
        error = ''
        null_flag = 1
        req_num = 0
        try:
            car_para_a, car_para_b, car_para_c, car_para_z = {}, {}, {}, {}
            standardize_car_int = reco_pretreatment.standardize_para(car_para)
            # key_set = set(standardize_car_int.keys())
            for key in standardize_car_int:
                temp_name = car_para_dict.get(key)
                temp_list = standardize_car_int[key].copy()
                if temp_list:
                    req_num += 1
                    null_flag = 0
                    locals()['car_para_' + temp_name][key] = temp_list
            favor_list = car_para_z.get('favor')  # 暂无优先级
            favor_order = [-1] * len(favor_list) if favor_list else 0
            a_return_id_list, b_return_id_list, c_return_id_list = [], [], []
            if car_para_a:
                a_return_id_list, a_return_list, null_flag_p = reco_db.find_car_model(car_para_a)
                null_flag *= null_flag_p
            if len(a_return_id_list) >= 1:
                if car_para_b:
                    b_return_id_list, b_return_list, null_flag_p = reco_db.find_car_model(
                        dict(car_para_a, **car_para_b))
                    null_flag *= null_flag_p
                if len(b_return_id_list) >= 1:
                    if car_para_c:
                        c_return_id_list, c_return_list, null_flag_p = reco_db.find_car_model(
                            dict(car_para_a, **car_para_b, **car_para_c))
                        null_flag *= null_flag_p
                    if len(c_return_id_list) >= 1:
                        if favor_list:
                            result_id_list, result_name_list = reco_db.favor_sort(c_return_id_list, favor_list,
                                                                                  favor_order)
                        else:
                            result_id_list = c_return_id_list
                            result_name_list = c_return_list
                        require_acc_list = list(car_para_a.keys()) + list(
                            car_para_b.keys()) + list(car_para_c.keys())
                        result_tag = 0
                    else:
                        if favor_list:
                            result_id_list, result_name_list = reco_db.favor_sort(b_return_id_list, favor_list,
                                                                                  favor_order)
                        else:
                            result_id_list = b_return_id_list
                            result_name_list = b_return_list
                        require_acc_list = list(car_para_a.keys()) + list(
                            car_para_b.keys())
                        result_tag = 3
                else:
                    if favor_list:
                        result_id_list, result_name_list = reco_db.favor_sort(a_return_id_list, favor_list, favor_order)
                    else:
                        result_id_list = a_return_id_list
                        result_name_list = a_return_list
                    require_acc_list = list(car_para_a.keys())
                    result_tag = 2
            else:
                if 'car_series' in car_para_a:
                    s_return_id_list, s_return_list, _ = reco_db.find_car_model(
                        {'car_series': car_para_a['car_series']})
                    # 不存在车系找不到的情况
                    if favor_list:
                        result_id_list, result_name_list = reco_db.favor_sort(s_return_id_list, favor_list, favor_order)
                    else:
                        result_id_list = s_return_id_list
                        result_name_list = s_return_list
                    require_acc_list = ['car_series']
                    result_tag = 1
                else:
                    result_id_list, result_name_list, _ = reco_db.find_car_model(
                        {})
                    result_tag = 4
                    result_flag = -1
            if not favor_list and null_flag:
                result_id_list, result_name_list, _ = reco_db.find_car_model(
                    {})
                result_tag = 5

            len_result_name_list = len(result_name_list)
            if len_result_name_list <= max_result_for_start_reco or req_num >= max_input_for_start_reco:
                result_flag += 1

            count = 0
            if not reco_his:
                reco_his = {}
            for re in zip(result_id_list, result_name_list):
                if reco_his.get(re[0]) != -1:
                    result_list.append({'model_id': re[0], 'model_name': re[1]})
                    count += 1
                if count >= cut_num:
                    break

            result_tag_dict = {'tag': result_tag, 'dsc': require_acc_list}
        except Exception as e:
            error = str(e)
            print(error)
            result_tag = -1
            require_acc_list = []
            result_tag_dict = {'tag': -1, 'dsc': []}
            traceback.print_exc()
        finally:
            rmd_rst.append(result_list)
            rst_dsc.append(result_tag_dict)
            rst_flag.append(result_flag)
            reco_db.write_log(car_para, reco_his, standardize_car_int, result_list, result_tag, require_acc_list, error,
                              start_time)
    return rmd_rst, rst_dsc, rst_flag


if __name__ == '__main__':
    rmd_rst, rst_dsc, rst_flag = reco_car_model(
        [{"car_series": ["途观"], "version": [], "year": ["2022款"], "liter": [], "gear_type": [], "body_type": [],
          "model_price": [], "model_space": [], "fuel_type": ["纯电"], "seat_number": [], "max_miles": ["400公里"],
          "favor": []}, {
             'car_series': [],
             'version': [],
             'year': ['2021款'],
             'liter': [],
             'gear_type': [],
             'body_type': ['轿车'],
             'model_price': ['200000', '300000'],
             'model_space': [],
             'fuel_type': ['新能源'],
             'seat_number': [],
             'favor': []
         }, {"car_series": [], "version": [], "year": ["2022款"], "liter": [],
             "gear_type": [], "body_type": ["SUV"], "model_price": ["300000"],
             "model_space": ["中型"], "fuel_type": ["新能源"], "seat_number": [],
             "favor": []}], {'1708797': -1, '1772284': -1})
    print(rmd_rst, rst_dsc, rst_flag)
