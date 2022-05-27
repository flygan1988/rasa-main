MYSQL_USER = "root"
MYSQL_PASSWORD = "password"
MYSQL_HOST = "10.116.47.86"
MYSQL_PORT = 3306
MYSQL_DBNAME = "carkb"

######slot names#############
SLOT_MENTION = "mention"
SLOT_OBJECT_TYPE = "object_type"
SLOT_ATTRIBUTE_LIST = "attribute"
SLOT_LISTED_OBJECTS = "knowledge_base_listed_objects"
SLOT_LAST_OBJECT = "knowledge_base_last_object"
SLOT_LAST_MODEL = "knowledge_base_last_model"
SLOT_LAST_OBJECT_TYPE = "knowledge_base_last_object_type"
SLOT_LISTED_MODELS = "knowledge_base_listed_models"
SLOT_SERIES_NAME_LIST = "series_name"
SLOT_MODEL_NAME = "model_name"
SLOT_SERIES_LEVEL = "series_level"
SLOT_SPACE = "space"
SLOT_PRICE = "price"
SLOT_ENGINE_POWER = "engine_power_kw"
SLOT_GEAR_TYPE = "gear_type"
SLOT_SEAT_NUMBER = "seat"
SLOT_RECO_HIS = "reco_his"
#######recommend parameters#########
RECOM_PARAMS = ['car_series',
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
RECOM_SLOT_MAP = {'car_series':'car',
        'version':'model_name',
        'year':'year',
        'liter':'liter',
        'gear_type':'gear_type',
        'body_type':'series_level',
        'model_price':'price',
        'model_space':'space',
        'fuel_type':'fuel_type',
        'seat_number':'seat_number',
        'max_miles':'max_miles',
        'favor':'favor'}
RECOM_CHI_MAP = {
        'car_series':'车系',
        'version':'车型版本',
        'year':'上市年份',
        'liter':'排量',
        'gear_type':'变速器类型',
        'body_type':'车身类型',
        'model_price':'价格',
        'model_space':'空间',
        'fuel_type':'能源类型',
        'seat_number':'座位个数',
        'max_miles':'续航里程',
        'favor':'偏好'
}
RECOM_UTTER_MAP = {
        0:'符合您要求的车有这些：',
        1:'目前满足您<b>{}</b>需求的车有这些：',
        2:'目前满足您<b>{}</b>需求的车有这些：',
        3:'目前满足您<b>{}</b>需求的车有这些：',
        4:'抱歉！目前没有能满足您需求的车子',
        5:'这边比较推荐：'
}