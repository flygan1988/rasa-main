import pandas as pd
from sqlalchemy import create_engine

host = '127.0.0.1'
port = 3306
db = 'che300'
user = 'root'
password = 'password'

engine = create_engine(str(r"mysql+mysqldb://%s:" + '%s' + "@%s/%s") % (user, password, host, db))

with engine.begin() as conn:
    df = pd.read_excel("C:\\Users\\ganfei\\Documents\\数字人\\che300_pc_models_v3.5.10758_en_v2.xlsx", sheet_name="series")
    df.to_sql(name="series", con=conn, index=False)

with engine.begin() as conn:
    df = pd.read_excel("C:\\Users\\ganfei\\Documents\\数字人\\che300_pc_models_v3.5.10758_en_v2.xlsx", sheet_name="maker")
    df.to_sql(name="maker", con=conn, index=False)

with engine.begin() as conn:
    df = pd.read_excel("C:\\Users\\ganfei\\Documents\\数字人\\che300_pc_models_v3.5.10758_en_v2.xlsx", sheet_name="series_group")
    df.to_sql(name="series_group", con=conn, index=False)

with engine.begin() as conn:
    df = pd.read_excel("C:\\Users\\ganfei\\Documents\\数字人\\che300_pc_models_v3.5.10758_en_v2.xlsx", sheet_name="area")
    df.to_sql(name="area", con=conn, index=False)

with engine.begin() as conn:
    df = pd.read_excel("C:\\Users\\ganfei\\Documents\\数字人\\che300_pc_models_v3.5.10758_en_v2.xlsx", sheet_name="model")
    df.to_sql(name="model", con=conn, index=False)

