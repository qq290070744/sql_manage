import os

inception_host = os.getenv('inception_host')
inception_port = os.getenv('inception_port')
inception_user = os.getenv('inception_user')
inception_pwd = os.getenv('inception_pwd')
if os.getenv('PYTHONENV') == 'prod':
    inception_host = '10.157.36.11'
    inception_port = 4000
    inception_user = 'root'
    inception_pwd = '123123'
elif os.getenv('PYTHONENV') == 'stage':
    inception_host = '10.157.26.55'
    inception_port = 4000
    inception_user = 'root'
    inception_pwd = '123123'
else:
    if not inception_host:
        inception_host = '127.0.0.1'
    if not inception_port:
        inception_port = 4000
    if not inception_user:
        inception_user = 'root'
    if not inception_pwd:
        inception_pwd = '123123'


def inception(user, password, host, port, db, sql, operate):
    import pymysql
    sql = '''
    /*--user={};--password={};--host={};--{}=1;--backup=1;--port={};ignore_warnings=1;*/
    inception_magic_start;
    use `{}`;
    {};
    inception_magic_commit;
    '''.format(user, password, host, operate, port, db, sql)
    conn = pymysql.connect(host=inception_host, user=inception_user, passwd=inception_pwd, port=inception_port,
                           charset="utf8mb4")
    cur = conn.cursor()
    ret = cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


if __name__ == '__main__':
    res = inception('root', '123123', '192.168.23.130', '3306', 'test', 'update test set id=1 ', 'check')
    print(res)
