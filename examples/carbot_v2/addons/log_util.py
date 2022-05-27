import sys
sys.path.append('../')
from utils.constants import MYSQL_USER, MYSQL_DBNAME, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT
from sqlalchemy import create_engine
import json

# knowledge_base = CarKnowledgeBase(MYSQL_DBNAME, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST)
# db_url = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME)
# data_engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)

def log():
    db_url = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT,MYSQL_DBNAME)
    data_engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)
    sql = "SELECT * FROM car300_model LIMIT 1"
    with data_engine.connect() as conn:
        res = conn.execute(sql)
    return [key for key in res.keys()]