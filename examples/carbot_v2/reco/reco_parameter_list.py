# -*- coding: utf-8 -*-
"""
Created on Wed May 11 10:38:50 2022

@author: Cynthia_66
"""

# 定期访问数据库，更新推荐系统映射表，并存储回数据库中
import pymysql
import traceback
import numpy as np
import pandas as pd
import sqlalchemy as sql
import os
import re
from sqlalchemy import create_engine
from datetime import datetime




#数据库
pymysql.install_as_MySQLdb()

db_host='10.116.47.86'
db_user='root'
db_password='password'
db_name='mysql'
db_port=3306
db_charset='utf8'
db_schema='carkb'

# 修改默认路径
# mypath='D:\\dataman\\recommend_system'  
# os.chdir(mypath)
# os.getcwd()


# 推荐入参列表
para_list=['car_series',
     'version',
     'year',
     'liter',
     'gear_type',
     'body_type',
     'model_price',
     'model_space',
     'fuel_type',
     'seat_number',
     'favor']


#
# =============================================================================
# sql1='''
# select a.series_group_name ,
# a.series_id  ,
# a.series_name ,
# a.model_id
# a.model_name ,
# a.model_year ,
# a.gear_type ,
# a.body_type ,
# b.car_level ,
# b.fuel_type ,
# a.seat_number ,
# a.liter,
# a.price
# from carkb.car300_model a
# left join carkb.car300_model_detail_parameter b 
# on a.model_id =b.model_id 
# where a.model_status ="在售"
# and a.series_group_name ="上汽大众"
# '''
# =============================================================================


sql1='''
with temp_1 as
(
select 
a.series_group_name ,
a.series_id  ,
a.series_name ,
a.model_id ,
a.model_name ,
a.model_year ,
a.gear_type ,
a.body_type as ini_body_type,
b.car_level ,
b.offical_battery_range_miles as max_miles, 
a.seat_number ,
a.liter,
a.price,
c.engine_power ,
c.wheel_base ,
c.fuel_type ,
c.seat_count ,
c.space_level ,
c.power_level ,
c.fashion_level ,
c.grade_level ,
c.business_level ,
c.outdoors_level ,
c.family_level ,
c.cp_level 
 from carkb.car300_model a
 left join carkb.car300_model_detail_parameter b
 on a.model_id =b.model_id 
 left join carkb.carkg_model_rule_tag c
 on a.model_id =c.model_id 
 where a.model_status ="在售"
 and a.series_group_name ="上汽大众"
 )
select * from 
(select t1.*,
 ROW_NUMBER() over(partition by model_id order by model_id) as rn
 from temp_1 t1
 )k
 where rn=1
'''


#%%
#定义读取函数
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
    conn = pymysql.connect(host=db_host, port=db_port, user=db_user,password=db_password,db=db_name)
 
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

df=mysql_to_df(sql1, db_host, db_user, db_password, db_name, db_port)

df2=df.copy(deep=True) #用于构造车型推荐参数表

#%%
#各个参数处理

#车系库列表,注意，有中英文 特殊字符，应在后续处理中保持一致
car_series=list(set(df.series_name))


#版本时间范围 
year=list(set(df.model_year))
year=[int(i) for i in year]

earlist_year=np.min(year)
latest_year=np.max(year)

#排量 liter,一位小数+L/T
# 0.0L 为新能源车
liter=list(set(df.liter))


#价格model_price
model_price=list(set(df.price))
model_price=[float(i) for i in model_price]

max_price=np.max(model_price)
min_price=np.min(model_price)

price=df['price'].apply(lambda x:round(float(x)*10000))
df2['price']=price

#变速器列表
gear_type=list(set(df.gear_type))



#车辆类别列表
#body_type=list(set(df.body_type))
#预定义好的格式
body_type=['轿车','SUV','MPV']
body_type_detail=['掀背','两厢','三厢']
cross_type=['跨界车']  #跨界标识

#拆分三列
df2['body_type']=np.nan
df2['body_type_detail']=np.nan
df2['cross_type']=np.nan

#逐行处理
for i in range(df2.shape[0]):
    ini_body_type_i=df2.ini_body_type[i]
    if ini_body_type_i=='SUV':
        df2.loc[i,'body_type']='SUV'
    elif ini_body_type_i=='SUV跨界车':
        df2.loc[i,'body_type']='SUV'
        df2.loc[i,'cross_type']='跨界车'
    elif ini_body_type_i=='MPV':
        df2.loc[i,'body_type']='MPV'
    elif ini_body_type_i=='三厢车':
        df2.loc[i,'body_type']='轿车'
        df2.loc[i,'body_type_detail']='三厢'
    elif ini_body_type_i=='两厢车':
        df2.loc[i,'body_type']='轿车'
        df2.loc[i,'body_type_detail']='两厢'
    elif ini_body_type_i=='掀背车':
        df2.loc[i,'body_type']='轿车'
        df2.loc[i,'body_type_detail']='掀背'
        


#能源类型列表
fuel_type=list(set(df.fuel_type))

#座位数量列表：int
seat_number=list(set(df.seat_number))


#版本列表,直取车名列表中带“版”字的部分，或者带“R-Line”的部分
model_name=list(set(df.model_name))

#定义函数：取出name中的version
def get_version(name):
    if len(name)==0:
        version=''
    else:
        nl=re.split(r'\s+', name) #按空格分词  
        for i in nl:
            if "版" in i or "R-Line" in i:
                version=i
    return version


#处理
version=list(set(map(get_version,model_name)))

df2['version']=df2['model_name'].apply(get_version)




#空间列表,预定义好，不随数据表更新
model_space=['小型','紧凑型','中型','中大型','大型']

def get_space(car_level):
    if len(car_level)==0:
        space=np.nan
    else:
        if '小型' in car_level:
            space='小型'
        elif '紧凑型' in car_level:
            space='紧凑型'
        elif '中大型' in car_level:
            space='中大型'
        elif '中型' in car_level:
            space='中型'
        elif '大型' in car_level:
            space='大型'
        else:
            space=np.nan
    return space

df2['space']=df2['car_level'].apply(get_space)

#续航里程
max_miles=list(set(df.max_miles))

max_miles_clean=[]
for i in max_miles:
    if len(i)>0:
        max_miles_clean.append(int(i))
        
max_miles_range=[min(max_miles_clean),max(max_miles_clean)]

#缺失值调整
#df2['max_miles_clean']=0

for i in range(df2.shape[0]):
    if len(df2.loc[i,'max_miles'])==0:
        df2.loc[i,'max_miles']=np.nan
    else:
        df2.loc[i,'max_miles']=int(df2.loc[i,'max_miles'])



#偏好列表(字典)，预定义好，不随数据表更新
#如果车型标签更新，再更新这个list
#favor=['空间大','动力足','时尚','性价比','高档','商务','越野','家庭']

favor_dict={
    'space_level':['空间大','大','宽敞'],
    'power_level':['动力足','动力充足','动力强'],
    'fashion_level':['时尚','好看','漂亮','时髦'],
    'CP_level':['性价比','性价比高'],
    'grade_level':['高档','档次高','有牌面'],
    'business_level':['商务','办公','老板','领导'],
    'outdoors_level':['越野','户外','山路'],
    'family_level':['家庭','座位多']
    }



#%%

# =============================================================================
# #参数导入df
# para_standard=pd.DataFrame(columns=['para_name','para_value'])
# 
#     
# #para_standard=para_standard.append({'para_name':'car_series','para_value':car_series},ignore_index=True)
# #检查下长度 len(str(para_standard.iloc[0,1]))
# 
# para_standard.loc[0]=['car_series',str(car_series)]
# para_standard.loc[1]=['version',str(version)]
# para_standard.loc[2]=['year',str(year)]
# para_standard.loc[3]=['liter',str(liter)]
# para_standard.loc[4]=['gear_type',str(gear_type)]
# para_standard.loc[5]=['body_type',str(body_type)]
# para_standard.loc[6]=['model_price',str([min_price,max_price])]
# para_standard.loc[7]=['model_space',str(model_space)]
# para_standard.loc[8]=['fuel_type',str(fuel_type)]
# para_standard.loc[9]=['seat_number',str(seat_number)]
# para_standard.loc[10]=['favor',str(favor_dict)]
# =============================================================================


#%%

#获取时间
ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
update_time = datetime.now().strftime(ISOTIMEFORMAT)  #获取当前系统时间
print(update_time)
# =============================================================================
# #导出到数据库中
# sql_connect = create_engine(r'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(db_user,db_password,db_host,db_port,db_name))
# 
# for i in range(para_standard.shape[0]):    
#     para_name=para_standard.para_name[i]
#     para_value=para_standard.para_value[i]
#     sql_0="INSERT INTO carkb.intrsys_para_standard_rule VALUES (%s,%s,%s)"
#     sql=sql_0 % (repr(para_name), repr(para_value),repr(update_time))    
#     sql_connect.execute(sql)
# =============================================================================


#导出到数据库中
sql_connect = create_engine(r'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(db_user,db_password,db_host,db_port,db_name))



#参数清洗规则表
sql_11="INSERT INTO reco.reco_para_standard_rule VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
sql_12=sql_11 % (repr(str(car_series)), 
             repr(str(version)),   
             repr(str(year)),   
             repr(str(liter)),   
             repr(str(gear_type)),   
             repr(str(body_type)),   
             repr(str(body_type_detail)),   
             repr(str(cross_type)),   
             repr(str([min_price,max_price])),   
             repr(str(model_space)),   
             repr(str(fuel_type)),   
             repr(str(seat_number)),   
             repr(str(favor_dict)),   
             repr(str(max_miles_range)),   
             repr(str(update_time)))   

sql_connect.execute(sql_12)

#车型推荐信息表

sql20 = "TRUNCATE TABLE reco.reco_model_info" 
sql21 = "INSERT INTO reco.reco_model_info VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
sql22 = "INSERT INTO reco.reco_model_info_his VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"


#先把需要插入的数据改成list格式
data_list=[]

df2 = df2.where(df2.notnull(), None)

for i in range(df2.shape[0]):
    tuple_i=(df2.loc[i,'series_group_name'],
            df2.loc[i,'series_id'],
            df2.loc[i,'series_name'],
            df2.loc[i,'model_name'],
            df2.loc[i,'model_id'],
            df2.loc[i,'model_year'],
            df2.loc[i,'gear_type'],
            df2.loc[i,'ini_body_type'],
            df2.loc[i,'car_level'],
            df2.loc[i,'seat_number'],
            df2.loc[i,'liter'],
            df2.loc[i,'price'],
            df2.loc[i,'engine_power'],
            df2.loc[i,'wheel_base'],
            df2.loc[i,'fuel_type'],
            df2.loc[i,'space_level'],
            df2.loc[i,'power_level'],
            df2.loc[i,'fashion_level'],
            df2.loc[i,'grade_level'],
            df2.loc[i,'business_level'],
            df2.loc[i,'outdoors_level'],
            df2.loc[i,'family_level'],
            df2.loc[i,'cp_level'],
            df2.loc[i,'body_type'],
            df2.loc[i,'body_type_detail'],
            df2.loc[i,'cross_type'],
            df2.loc[i,'version'],
            df2.loc[i,'space'],
            df2.loc[i,'max_miles'],
            str(update_time))
    data_list.append(tuple_i)


#将list批量插入


# 打开数据库连接

db = pymysql.connect(host=db_host, port=3306,
           user=db_user, passwd=db_password, db=db_name, charset='utf8')
cursor = db.cursor()

cursor.execute(sql20)
cursor.executemany(sql21,data_list)
cursor.executemany(sql22,data_list)

db.commit()
cursor.close()
db.close()

#%% 
#导出到xlsx或csv
#para_standard.to_excel("附件1_副本.xlsx", index=False)
#para_standard.to_csv("附件1_副本.csv", index=False,encoding="utf_8_sig")
 
#%%
#生成车型推荐表
#存储大众在售车型，推荐相关的所有参数

#df2=mysql_to_df(sql2, db_host, db_user, db_password, db_name, db_port)

