from sqlalchemy import create_engine


host = '127.0.0.1'
port = 3306
db = 'che300'
user = 'root'
password = 'password'

engine = create_engine(str(r"mysql+mysqldb://%s:" + '%s' + "@%s/%s") % (user, password, host, db))


def get_model_by_series_name(series_name):
    """按照车型获取车子参数，解决如：途观多少钱？ 途观动力怎样？ 等问题
       默认返回最新款车型
    """
    sql = "SELECT * FROM model where series_name = '{}' and `year` = (select max(`year`) from model)".format(series_name)
    res = engine.execute(sql)
    return [dict(zip(res.keys(), result)) for result in res]

def get_series_by_brand_name(brand_name):
    """按照品牌获取车系，如：奥迪有哪些车系"""
    sql = "SELECT * FROM series where brand_name = '{}'".format(brand_name)
    res = engine.execute(sql)
    return [dict(zip(res.keys(), result)) for result in res]





if __name__ == '__main__':
    res = get_model_by_series_name('奥迪A4L')

    print(len(res))
    print(res[:1])
    # model_year = res[0]['model_year']
    # data = list(filter(lambda car: car['model_year'] == model_year, res))
    # print(data)