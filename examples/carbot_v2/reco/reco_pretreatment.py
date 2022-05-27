# -*- coding: utf-8 -*-
"""
Created on Fri May  6 13:15:15 2022

@author: Cynthia_66
"""

# 仅针对上汽大众车型，输出清洗结果
# 超出范围的资料无法识别


import pymysql
import re
import cn2an
import datetime
import numpy as np
import pandas as pd
import traceback

# 数据库连接

db_host = '10.116.47.86'
db_user = 'root'
db_password = 'password'
db_name = 'mysql'
db_port = 3306
db_charset = 'utf8'
db_schema = 'carkb'

#价格浮动区间
round_size=0.2

# 推荐入参列表
# 如果进行变更需要增加相应的清洗方法，命名为standardize_eval(para)
para_list = ['car_series',
             'version',
             'year',
             'liter',
             'gear_type',
             'body_type',
             'model_price',
             'model_space',
             'fuel_type',
             'seat_number',
             'max_miles',
             'favor']


# 定义读取函数
def mysql_to_df(sql, db_host, db_user, db_password, db_name, db_port=3306):
    """将sql查询结果转成DataFrame    
    param sql:sql查询语句
    param host:mysql连接ip
    param user:用户名
    param password:密码
    param db_name:需要使用的数据库
    param port:端口,默认3306
    return df:查询结果，DateFrame格式
    """
    # 打开数据库连接
    conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_password, db=db_name)

    try:
        results = pd.read_sql(sql, con=conn)
        print(results.head(10))
        conn.close()

        return results
    except:
        print("=====错误，请检查sql代码=====")
        # 打印错误信息
        traceback.print_exc()
        # 如果发生错误则回滚
        conn.rollback()
        conn.close()


sql1 = '''
select * from reco.reco_para_standard_rule
order by update_time desc limit 1
'''

df = mysql_to_df(sql1, db_host, db_user, db_password, db_name, db_port)


# %%
# 定义list转化函数

def string_to_list(string):
    # 数据库中获取的list为string格式，转化成list格式
    mylist = string.replace("[", "")  # 删掉[
    mylist = mylist.replace("]", "")  # 删掉]
    mylist = mylist.replace("'", "")  # 删掉 '
    mylist = mylist.split(", ")  # 切分
    return mylist


# 车系库列表
car_series_list = string_to_list(df.car_series[0])

# 版本列表
version_list = string_to_list(df.version[0])

# 版本时间范围
year_list = string_to_list(df.year[0])
year_list = [int(i) for i in year_list]

earlist_year = min(year_list)
latest_year = max(year_list)

# 变速器列表
gear_type_list = string_to_list(df.gear_type[0])

# 车辆类别列表
body_type_list = string_to_list(df.body_type[0])  # todo :检查结构
#  ['掀背车', 'SUV', '两厢车', '三厢车', 'MPV', 'SUV跨界车']


# 空间列表
space_list = string_to_list(df.model_space[0])

# 能源类型列表
fuel_type_list = string_to_list(df.fuel_type[0])

# 座位数量列表：int
seat_number_list = string_to_list(df.seat_number[0])
seat_number_list = [int(i) for i in seat_number_list]

# 偏好列表(字典)
favor_list = eval(df.favor[0])

# 字典倒序
favor_list_inverse = {}
for key, value in favor_list.items():
    if len(value) > 0:
        for i in value:
            if i in favor_list_inverse.keys():
                favor_list_inverse[i].append(key)
            else:
                favor_list_inverse[i] = [key]


# %%

# 标准化主函数
def standardize_para(car_int):
    """
    用于数据清洗标准化，输入相关参数存入para，类型为dict，键名参照对话系统传入参数，不包含favor？
    返回标准化后的参数，如果标准化后没有匹配则不返回该键
    """
    car_int_clean = {}
    if len(car_int) == 0:
        print('入参全部为空！')
    else:
        mykeys = list(car_int.keys())  # 取出car_int中有的值
        for key in para_list:
            if key not in mykeys:  # 如果入参里没有这个参数
                car_int_clean[key] = []  # 清洗结果返回空列表
            else:  # 如果入参里有
                car_int_clean[key] = standardize_one_para(key, car_int[key])
                # 另建议每个参数清洗单独封装方法，便于修改
    return car_int_clean


# 对每个字段，用对应的函数处理
def standardize_one_para(key, ini_para):
    clean_para = []
    if key in para_list:
        clean_para = eval('standardize_' + key)(ini_para)
    return clean_para


# 文本预处理-只保留汉字

# 判断字符是否为汉字
def is_chinese(uchar):
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False


# 取出文本中的所有汉字
def format_str(content):
    content_str = ''
    for i in content:
        if is_chinese(i):
            content_str = content_str + i
    return content_str


# 取出文本中所有汉字 数字 字母，字母转小写
def fromat_str_2(content):
    pattern = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9]")  # 只保留中英文、数字，去掉其他东西
    content = content.lower()  # 转小写
    content_str = re.sub(pattern, '', content)  # 把文本中匹配到的字符去掉
    #    content=''.join(content.split())    #去除空白
    return content_str


# %%

# 每个字段定义标准化函数，再通过主函数调用

# 车系 car_series，清洗输入参数，返回所有包含这个词的车系，支持入参为多个词,返回结果为车系list
car_series_list_2 = [fromat_str_2(i) for i in car_series_list]


def standardize_car_series(ini_carseries):
    '''
    car_series参数清洗，返回清洗结果
    '''
    clean_carseries = []
    for i in ini_carseries:  # 逐个车系处理
        if not isinstance(i, str):
            i = str(i)
        ic = fromat_str_2(i)  # 只保留汉字，数字，小写英文字母
        # 检查是否在车系列表里
        for j in range(len(car_series_list_2)):
            if ic in car_series_list_2[j]:
                clean_carseries.append(car_series_list[j])  # 清洗结果中，添加该车系
    return clean_carseries


# standardize_car_series(['途观', 'id.3'])


# 版本 version，清洗输入参数，返回所有包含这个词的版本，支持入参为多个词,返回结果为版本list
version_list_2 = [fromat_str_2(i) for i in version_list]


def standardize_version(ini_version):
    '''
    version参数清洗，返回清洗结果list
    '''
    clean_version = []
    for i in ini_version:  # 逐个单词处理
        if not isinstance(i, str):
            i = str(i)
        ic = fromat_str_2(i)  # 只保留汉字，数字，小写英文字母
        # 检查是否在车系列表里
        for j in range(len(version_list_2)):
            if ic in version_list_2[j]:
                clean_version.append(version_list[j])  # 清洗结果中，添加该车系
    return clean_version


# standardize_version(['续航','纯净'])

# 年份 year
# 处理结果为纯数字，只处理>=2000年，超出year_list范围不返回
# 2021年：2021 完成
# 21年： 2021 完成
# 1998年： 1998 完成
# 1998： []
# 二一年：2021 完成
# 二零二一： 2021 完成
# 2021款：2021 完成


# todo:从数据库中获取最新版本时间，版本时间范围，


def standardize_year(ini_year):
    '''
    year参数清洗，返回清洗结果
    '''
    clean_year = []
    this_year = datetime.date.today().year  # 获取当前年份
    year_list = [i for i in range(2000, this_year + 1)]  # todo todo 存在提前发售？
    for i in ini_year:
        # print(i)
        if not isinstance(i, str):
            i = str(i)
        if '今年' in i:  # "今年"的特殊处理
            clean_year.append(this_year)
        # 数字部分处理
        ic = re.sub("\D", "", i)  # 只保留数字
        if len(ic) > 0:
            # print('数字部分')
            ic = int(ic)
            if ic in year_list:  # 时间在范围内:[2000,今年]
                clean_year.append(ic)
            elif ic in [i % 100 for i in year_list]:  # 如果客户说 21年
                clean_year.append(2000 + ic)
        # 中文部分处理
        icc = format_str(i)
        if len(icc) > 0:
            # print('汉字部分')
            icc = cn2an.transform(icc)  # 中文转数字
            icc = re.sub("\D", "", icc)  # 只保留数字
            if len(icc) > 0:
                icc = int(icc)
                if icc in year_list:  # 时间在范围内:[2000,今年]
                    clean_year.append(icc)
                elif icc in [i % 100 for i in year_list]:  # 如果客户说 21年
                    clean_year.append(2000 + icc)
    clean_year = list(set(clean_year))  # 去重
    return clean_year


# standardize_year(['21年','2021','二零年'])

# 排量 liter,一位小数+L/T，如果输入中未明确L或T，输出L和T两个元素

def standardize_liter(ini_liter):
    '''
    liter参数清洗，返回清洗结果
    '''
    clean_liter = []
    for i in ini_liter:
        if not isinstance(i, str):
            i = str(i)
        ic = cn2an.transform(i)  # 中文转数字
        # 数字部分
        i_n = ''.join(filter(lambda i: i in ['.'] or i.isdigit(), ic))  # 只保留数字和小数点
        i_n_f = i_n.replace('.', '')  # 去掉小数点之后的数字部分
        if len(i_n_f) > 0:  # 如果有数字
            if float(i_n) >= 0 and float(i_n) <= 10:  # 限制范围，[0,10]
                # 汉字部分
                if 't' in ic or 'T' in ic:
                    clean_liter.append(str(i_n) + 'T')
                elif 'l' in ic or 'L' in ic or '升' in ic:
                    clean_liter.append(str(i_n) + 'L')
                else:
                    clean_liter.append(str(i_n) + 'L')
                    clean_liter.append(str(i_n) + 'T')
    return clean_liter


# standardize_liter(['1.5升','一点六t','1.2t','1.4'])

# 变速器 gear_type,不调用list
def standardize_gear_type(ini_gear_type):
    '''
    gear_type参数清洗，返回清洗结果
    '''
    clean_gear_type = []
    for i in ini_gear_type:
        if not isinstance(i, str):
            i = str(i)
        ic = format_str(i)  # 只保留汉字
        if '手动' in ic:
            clean_gear_type.append('手动')
        elif '自动' in ic:
            clean_gear_type.append('自动')
    return clean_gear_type


standardize_gear_type(['手动','自动d','手动挡'])
# standardize_gear_type(['手动','自动d','手动挡'])


# 车辆类别 body_type，固定list

# =============================================================================
# # body_type_list=[ 'SUV','MPV','SUV跨界车','轿车', '两厢车', '三厢车','掀背车']
# def standardize_body_type(ini_body_type):
#     '''
#     body_type参数清洗，返回清洗结果
#     '''
#     clean_body_type = []
#     for i in ini_body_type:
#         if not isinstance(i, str):
#             i = str(i)
#         ic = i.lower()  # 英文转小写
#         if 'suv跨界' in ic:
#             clean_body_type.append('SUV跨界车')
#         elif 'suv' in ic:
#             clean_body_type.append('SUV')
#         elif 'mpv' in ic:
#             clean_body_type.append('MPV')
#         elif '两厢' in ic:
#             clean_body_type.append('两厢车')
#         elif '三厢' in ic:
#             clean_body_type.append('三厢车')
#         elif '掀背' in ic:
#             clean_body_type.append('掀背车')
#         elif '轿车' in ic:
#             clean_body_type.append('轿车')
#     return clean_body_type
# 
# =============================================================================


#需要把 body_type  body_type_detail cross_type的关键词全部抓出来，放到这个表里
# suv跨界车： suv 跨界车
# 两箱车：两箱 轿车
# 掀背车：掀背 轿车
# 


def standardize_body_type(ini_body_type):
    '''
    body_type参数清洗，返回清洗结果
    '''
    clean_body_type = []
    for i in ini_body_type:
        clean_body_type_i=[]
        if not isinstance(i, str):
            i = str(i)
        ic = i.lower()  # 英文转小写
        if "suv" in ic:
            clean_body_type_i.append('SUV')            
        if "mpv" in ic:
            clean_body_type_i.append('MPV')         
        if "轿车" in ic:
            clean_body_type_i.append('轿车')
        if "跨界" in ic:
            clean_body_type_i.append('跨界车')   
        if "两厢" in ic:
            clean_body_type_i.append('两厢')
            if 'SUV' not in clean_body_type_i and 'MPV' not in clean_body_type_i:
                clean_body_type_i.append('轿车')
        if "三厢" in ic:
            clean_body_type_i.append('三厢')
            if 'SUV' not in clean_body_type_i and 'MPV' not in clean_body_type_i:
                clean_body_type_i.append('轿车')
        if "掀背" in ic:
            clean_body_type_i.append('掀背')
            if 'SUV' not in clean_body_type_i and 'MPV' not in clean_body_type_i:
                clean_body_type_i.append('轿车') 
        if len(clean_body_type_i)>0:
            clean_body_type_i=list(set(clean_body_type_i))
            clean_body_type.append(clean_body_type_i)
    return clean_body_type


# standardize_body_type(['两厢车','三厢跨界mpv'])
# standardize_body_type(['跑车'])
# standardize_body_type(['跑车','轿车跨界'])


# 车价 model_price
# 十三万二千 132000
# 11万5千 115000
# 23 230000
# 11.5万 115000
# 三万一百二十三 XX

# 0个清洗结果，返回空列表
#  只有一个清洗结果，上下浮动round_size
# 两个及以上清洗结果，返回 [min,max]

def standardize_model_price(ini_price):
    '''
    model_price参数清洗，返回清洗结果
    '''
    clean_price = []
    for i in ini_price:
        if not isinstance(i, str):
            i = str(i)
        try:
            ic = cn2an.cn2an(i, "smart")
            if len(str(ic)) > 0:
                if ic < 1000:
                    clean_price.append(int(ic * 10000))
                else:
                    clean_price.append(int(ic))
        except:
            continue
    if len(clean_price)==0:
        clean_price_range=[]
    elif len(clean_price)==1:
        clean_price_range=[int((1-round_size)*clean_price[0]),int((1+round_size)*clean_price[0])]
    else:
        clean_price_range=[min(clean_price),max(clean_price)]
    return clean_price_range


#standardize_model_price(['十三万二千','11万5千','23','三万一百二十三','11.5万'])
#standardize_model_price(['天气真不错'])
#standardize_model_price(['200000','300000'])

# 续航里程
def standardize_max_miles(ini_max_miles):
    '''
    max_mile参数清洗，返回清洗结果
    '''
    clean_max_miles=[]
    for i in ini_max_miles:
        if not isinstance(i, str):
            i = str(i)
        try:
            print(i)
            # 数字部分处理
            ic = re.sub("\D", "", i)  # 只保留数字
            if len(ic) > 0:
                ic = int(ic)
                clean_max_miles.append(ic)
            # 中文部分处理
            icc = format_str(i)
            if len(icc) > 0:
                icc = cn2an.transform(icc)  # 中文转数字
                icc = re.sub("\D", "", icc)  # 只保留数字
                if len(icc) > 0:
                    icc = int(icc)
                    clean_max_miles.append(icc)                
        except:
            continue
    clean_max_miles = list(set(clean_max_miles)) 
    return clean_max_miles


#standardize_max_miles(['200公里','350km','三百公里'])


# 空间 model_space
def standardize_model_space(ini_space):
    '''
    model_space参数清洗，返回清洗结果
    '''
    clean_space = []
    for i in ini_space:
        if not isinstance(i, str):
            i = str(i)
        ic = format_str(i)  # 只保留汉字
        if ic in space_list:  # todo:数据库中读取space_list
            clean_space.append(ic)
    return clean_space


# 能源类型 fuel_type
# fuel_type_list=['汽油','电力','油电']

def standardize_fuel_type(ini_fuel_type):
    '''
    fuel_type参数清洗，返回清洗结果
    '''
    clean_fuel_type = []
    for i in ini_fuel_type:
        if not isinstance(i, str):
            i = str(i)
        if '汽油' in i or '燃油' in i:
            clean_fuel_type.append('汽油')
        elif '混动' in i or '油电' in i:
            clean_fuel_type.append('油电')
        elif '电' in i:
            clean_fuel_type.append('电力')
        elif  '新能源' in i:
            clean_fuel_type.append('电力')
            clean_fuel_type.append('油电')
    clean_fuel_type=list(set(clean_fuel_type))        
    return clean_fuel_type

#standardize_fuel_type(['油电','新能源'])

# 座位个数 model_space，返回正整数，100以内
def standardize_seat_number(ini_seat_number):
    '''
    seat_number参数清洗，返回清洗结果
    '''
    clean_seat_number = []
    for i in ini_seat_number:
        if not isinstance(i, str):
            i = str(i)
        ic = cn2an.transform(i)  # 中文转数字
        ic = re.sub("\D", "", ic)  # 只保留数字
        if len(ic) > 0:
            ic = int(ic)
            if ic > 0 and ic <= 100:
                clean_seat_number.append(ic)
    return clean_seat_number


# standardize_seat_number(['五座','十座'])


# favor的标准化,需要考虑的情况比较复杂，先简单处理

# 用户偏好 favor
def standardize_favor(ini_favor):
    '''
    favor参数清洗，返回清洗结果
    '''
    clean_favor = []
    for i in ini_favor:
        if not isinstance(i, str):
            i = str(i)
        ic = format_str(i)  # 只保留汉字
        if ic in favor_list_inverse.keys():
            clean_favor.append(favor_list_inverse[ic][0])
    return clean_favor


# standardize_favor(['动力强','性价比高'])

# %%

# 模拟入参

if __name__ == '__main__':
    car_int = {'car_series': ['途观'],  # 车系
               'version': ['风尚版'],  # 版本
               'year': ['今年'],  # 发行年份
               'liter': ['1.4T'],  # 排量
               'gear_type': ['自动'],  # 手自动
               'body_type': ['suv'],  # 车辆类别：轿车 suv
               'model_price': ['二十万'],  # 价格
               'model_space': ['紧凑型'],  # 空间
               'fuel_type': ['汽油车'],  # 能源类型
               'seat_number': ['7座'],  # 座位个数
               'max_miles':['三百公里'], # 续航
               'favor': ['性价比高', '空间大']  # 用户偏好
               }

    # 测试
    print(standardize_para(car_int))
