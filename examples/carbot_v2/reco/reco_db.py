# -*- coding:utf-8 -*-
# mysql数据库，从文件读取配置
import os
import datetime
import json
import random

import numpy
import pymysql
import configparser


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


def get_config():
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_path, 'Config/config.ini')
    conf_info = configparser.ConfigParser()
    conf_info.read(config_file, encoding="utf-8")
    return conf_info


def find_car_model(car_info: dict) -> tuple:
    """
    用于主函数查询数据库匹配，输入相关参数存入para，类型为dict，键名参照对话系统传入参数
    返回符合条件的车型list
    """
    conf_info = get_config()
    host = eval(conf_info.get('mysql', 'host'))
    user = eval(conf_info.get('mysql', 'user'))
    password = eval(conf_info.get('mysql', 'password'))
    db = eval(conf_info.get('mysql', 'db'))
    port = eval(conf_info.get('mysql', 'port'))
    charset = eval(conf_info.get('mysql', 'charset'))

    key_name_dict = eval(conf_info.get('query', 'key_name_dict'))

    conn = pymysql.connect(user=user,
                           password=password,
                           host=host,  # 写你数据库的ip地址
                           database=db,
                           port=port,
                           charset=charset,  # 注意，只能为utf8, 不能是utf-8
                           cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    sql = '''select model_id, model_name from reco.reco_model_info where 1=1 '''
    null_flag = 1  # todo 是否有必要计算全空 兜底是否一定触发
    for key in car_info.keys():
        key_name = key_name_dict.get(key)
        if key_name:
            if key == 'model_price':
                price_list = car_info[key]
                if price_list:
                    null_flag = 0
                    sql += ('and ' + key_name + ' >= ' + str(price_list[0]) + ' '
                            + 'and ' + key_name + ' <= ' + str(price_list[1]) + ' ')
            elif key == 'body_type':
                body_type_list = car_info[key]
                if body_type_list:
                    null_flag = 0
                    sql += ' and ('
                    for target_list in body_type_list:
                        sql += '('
                        for target in target_list:
                            sql += '('
                            for key_name_detail in key_name:
                                sql += key_name_detail + ' = \'' + target + '\' or '
                            sql = sql[:-3]
                            sql += ') and '
                        sql = sql[:-4]
                        sql += ') or '
                    sql = sql[:-3]
                    sql += ')'
            elif key == 'max_miles':
                miles_list = car_info[key]
                if miles_list:
                    null_flag = 0
                    max_miles_str = str(max(miles_list))
                    sql += 'and (' + key_name + ' is null or ' + key_name + ' >= ' + max_miles_str + ') '
            else:
                # todo 未处理新增字段
                find_list = car_info[key]
                if find_list:
                    null_flag = 0
                    if len(find_list) == 1:
                        find_list.append('exception_blank_plx')
                    find_list_str = str(tuple(find_list))
                    sql += 'and ' + key_name + ' in ' + find_list_str + ' '
        else:
            print('未找到%s映射' % key)
    cursor.execute(sql)
    result = cursor.fetchall()  # 随机打乱 todo
    random.shuffle(result)
    result_model_id = [i['model_id'] for i in result]
    result_model_name = [i['model_name'] for i in result]
    cursor.close()
    conn.close()
    return result_model_id, result_model_name, null_flag


def favor_sort(model_id_list: list, favor_list: list, order_list: list) -> (list,list):
    """
    :param model_id_list: 车型id列表
    :param favor_list: 喜好列表，经过标准化与数据库字段相匹配。
    :param order_list: 排序方向，1表示正序，-1表示逆序
    :return: 排序后车型列表
    用于主函数调用排序
    """
    conf_info = get_config()
    host = eval(conf_info.get('mysql', 'host'))
    user = eval(conf_info.get('mysql', 'user'))
    password = eval(conf_info.get('mysql', 'password'))
    db = eval(conf_info.get('mysql', 'db'))
    port = eval(conf_info.get('mysql', 'port'))
    charset = eval(conf_info.get('mysql', 'charset'))

    conn = pymysql.connect(user=user,
                           password=password,
                           host=host,  # 写你数据库的ip地址
                           database=db,
                           port=port,
                           charset=charset,  # 注意，只能为utf8, 不能是utf-8
                           cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    model_id_str = str(tuple(model_id_list))
    order_str = ''
    for favor, order in zip(favor_list, order_list):
        order_str += favor + ' desc' if order == -1 else ''

    sql = '''select model_id, model_name from reco.reco_model_info
         where model_id in %s ''' % model_id_str

    if order_str:
        sql += 'order by %s ' % order_str

    cursor.execute(sql)

    result_model_id = []
    result_model_name = []

    for i in cursor.fetchall():
        result_model_name.append(i['model_name'])
        result_model_id.append(i['model_id'])
    cursor.close()
    conn.close()
    return result_model_id, result_model_name


def write_log(car_para, reco_his, standardize_car_int, result_list, result_tag, require_acc_list, error, start_time):
    conf_info = get_config()
    host = eval(conf_info.get('mysql', 'host'))
    user = eval(conf_info.get('mysql', 'user'))
    password = eval(conf_info.get('mysql', 'password'))
    db = eval(conf_info.get('mysql', 'db'))
    port = eval(conf_info.get('mysql', 'port'))
    charset = eval(conf_info.get('mysql', 'charset'))

    conn = pymysql.connect(user=user,
                           password=password,
                           host=host,  # 写你数据库的ip地址
                           database=db,
                           port=port,
                           charset=charset,  # 注意，只能为utf8, 不能是utf-8
                           cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    return_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if error:
        sql = '''insert into reco.reco_log(car_para,reco_his,standard_rst,result_list
                                                    ,result_tag,result_require_acc,remarks,create_time,return_time)
                        values ('%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', '%s')
                ''' % (
            json.dumps(car_para, ensure_ascii=False, cls=MyEncoder),
            json.dumps(reco_his, ensure_ascii=False, cls=MyEncoder),
            json.dumps(standardize_car_int, ensure_ascii=False, cls=MyEncoder),
            json.dumps(result_list, ensure_ascii=False, cls=MyEncoder),
            json.dumps(result_tag, ensure_ascii=False, cls=MyEncoder),
            json.dumps(require_acc_list, ensure_ascii=False, cls=MyEncoder),
            error.replace('\'', '\"') if len(error) <= 250 else error.replace('\'', '\"')[:250],
            start_time,
            return_time)
        cursor.execute(sql)
        cursor.close()
        conn.commit()
        conn.close()
    else:
        sql = '''insert into reco.reco_log(car_para,reco_his,standard_rst,result_list
                                            ,result_tag,result_require_acc,remarks,create_time,return_time)
                values ('%s', '%s', '%s', '%s', %s, '%s', %s, '%s', '%s')
        ''' % (
            json.dumps(car_para, ensure_ascii=False, cls=MyEncoder),
            json.dumps(reco_his, ensure_ascii=False, cls=MyEncoder),
            json.dumps(standardize_car_int, ensure_ascii=False, cls=MyEncoder),
            json.dumps(result_list, ensure_ascii=False, cls=MyEncoder),
            json.dumps(result_tag, ensure_ascii=False, cls=MyEncoder),
            json.dumps(require_acc_list, ensure_ascii=False, cls=MyEncoder),
            'NULL', start_time,
            return_time)
        cursor.execute(sql)
        cursor.close()
        conn.commit()
        conn.close()
    return None
