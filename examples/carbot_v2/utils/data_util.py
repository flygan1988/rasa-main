from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


host = '10.116.47.86'
port = 3306
db = 'carkb'
user = 'root'
password = 'password'

db_url = "mysql+mysqldb://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, db)
engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)
# engine = create_engine(str(r"mysql+mysqldb://%s:" + '%s' + "@%s/%s") % (user, password, host, db))

def get_model_by_series_name(series_name):
    """按照车型获取车子参数，解决如：途观多少钱？ 途观动力怎样？ 等问题
       默认返回最新款车型
    """
    sql = "SELECT * FROM model where series_name = '{}' and `year` = (select max(`year`) from model)".format(series_name)
    res = engine.execute(sql)
    return [dict(zip(res.keys(), result)) for result in res]

def get_series_by_brand_name(brand_name):
    """按照品牌获取车系，如：奥迪有哪些车系"""
    sql = "SELECT * FROM car300_series where brand_name = '{}'".format(brand_name)
    with engine.connect() as conn:
        res = conn.execute(sql)
    return [dict(zip(res.keys(), result)) for result in res]





if __name__ == '__main__':
    res = get_series_by_brand_name('大众')
    #
    # print(res)
    # print(res['content'])
    # print(res[:1])
    # model_year = res[0]['model_year']
    # data = list(filter(lambda car: car['model_year'] == model_year, res))
    # print(data)