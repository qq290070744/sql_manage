FROM python:3
#FROM registry.cn-shanghai.aliyuncs.com/jwh/sql_platform:20210813
WORKDIR /app
COPY . /app
RUN mv soar /bin/soar && chmod +x /bin/soar
RUN apt-get update && apt-get install -y percona-toolkit mariadb-client
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
EXPOSE 8000
ENV TZ Asia/Shanghai
ENV PYTHONENV prod
CMD [ "uvicorn", "main:app" ,"--host","0.0.0.0","--port","8000"]