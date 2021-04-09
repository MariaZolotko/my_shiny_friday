from enum import Enum

apikey='8803784b-fa83-4b12-8060-37049f25ef5d'
apikey1='0949a9ad-718d-4f48-ba42-a5d8845724cc'
token='1612045998:AAGRwNSrjbl9TVdxLkhS7vH4qm1CnCl4WuA'
db_file='database.vdb'


class States(Enum):
    S_START = "1"
    S_ENTER_GEO = "2"
    S_RECEIVE_GEO = "3"
    S_ENTER_BOUNDS = "4"
