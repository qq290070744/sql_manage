from pymysql import connect
from pymysql.cursors import DictCursor
from fastapi import HTTPException
from database.config import pymysql_config


def get_sqlcount():
    try:
        con = pymysql_config('inception')
        # con = connect(user='root',password='123123',host='192.168.23.130',port=3306,database='inception')
        cur = con.cursor(DictCursor)
        flag = cur.execute(
            'select  sum(deleting)  as `Delete_DML` ,sum(inserting) as `Insert_DML`,sum(updating) as `Update_DML`,sum(altertable) as AlterTable_DDL,sum(createindex) as CreateIndex_DDL,sum(addcolumn) as AddColumn_DDL,sum(changecolumn) as ChangeColumn_DDL,sum(createtable) as CreateTable_DDL from statistic;')
        res = cur.fetchall()
        print(res[0])
        res = [{'name': key, 'value': val} for key, val in res[0].items()]
        print(res)
        cur.close()
        con.close()
        return {'data': res, 'msg': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
