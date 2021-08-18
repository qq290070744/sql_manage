from fastapi import FastAPI, Depends, HTTPException
from starlette.middleware.cors import CORSMiddleware
from utils.menu_list import menu_list
from apps.user.user import usr
from apps.instance.instance import ins
from apps.role.role import role
from apps.user.user import get_user_role
from apps.query.query import que
from apps.inspect.inspect import insp
from apps.workorder.workorder import wkod
from apps.dashboard.dashboard import dash
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import os, time
from utils.AES_ECB_pkcs7_128 import en_pwd, de_pwd
from apps.goInception.goInception import go_inception
from apps.desensitization.desensitization import desensitization
import threading
from database.config import pymysql_config, mysql_db, exec_sql
from apps.slow_log.slow_log import slowlog
from typing import List
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

app.include_router(ins, prefix='/api/v1', tags=['instance'])
app.include_router(usr, prefix='/api/v1', tags=['user'])
app.include_router(role, prefix='/api/v1', tags=['role'])
app.include_router(que, prefix='/api/v1', tags=['query'])
app.include_router(insp, prefix='/api/v1', tags=['inspect'])
app.include_router(wkod, prefix='/api/v1', tags=['workorder'])
app.include_router(dash, prefix='/api/v1', tags=['dashboard'])
app.include_router(go_inception, prefix='/api/v1', tags=['goInception'])
app.include_router(desensitization, prefix='/api/v1', tags=['desensitization'])
app.include_router(slowlog, prefix='/api/v1', tags=['slowlog'])


@app.post('/api/v1/menu/')
def get_menu(role: str = Depends(get_user_role)):
    return {'data': menu_list[role], 'msg': 'success'}


@app.post('/api/v1/menu')
def get_menu(role: str = Depends(get_user_role)):
    return {'data': menu_list[role], 'msg': 'success'}


def start_goInception():
    cmd = '''ps aux|grep goInception|grep -v grep || ./goInception -config=apps/goInception/config.toml'''
    os.system(cmd)


@app.get('/', response_class=HTMLResponse)
def index_html():
    # t = threading.Thread(target=start_goInception)
    # t.start()
    if os.path.isfile("./dist/index.html"):
        with open("./dist/index.html", encoding='utf-8') as f:
            return f.read()


@app.get('/ping')
def ping():
    try:
        con = pymysql_config(mysql_db)
        cur = con.cursor()
        cur.execute("select 1")
        cur.close()
        con.close()
        return {'data': cur.fetchall(), 'msg': 'success', 'status': 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# app.mount("/data_export", StaticFiles(directory="data_export"), name="data_export")
@app.get("/data_export/{filename}")
def data_export(filename: str):
    file_path = os.path.join("data_export", filename)
    if os.path.isfile(file_path):
        file_like = open(file_path, mode="rb")

        def rm_file():
            time.sleep(100)
            os.remove(file_path)
            exec_sql(
                "update `workorder_data_export` set `download_time`='{}',`status`=3 where `path`='{}' ".format(time.strftime("%F %T"), file_path))

        t = threading.Thread(target=rm_file)
        t.start()

        return StreamingResponse(file_like, media_type="text/csv")


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    for file in files:
        # print(file.file.read())
        with open('/tmp/' + file.filename, mode="wb") as w:
            w.write(file.file.read())
    return {"filenames": [file.filename for file in files]}


@app.get("/upload_files")
async def upload_files():
    content = """
<body>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


app.mount("/", StaticFiles(directory="dist"), name="/")

if __name__ == "__main__":
    import uvicorn

    print(os.getenv('PYTHONENV'))
    uvicorn.run(app, host="0.0.0.0", port=8000)
