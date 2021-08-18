uvicorn main:app --reload --host 0.0.0.0

# docker
docker build -t registry.cn-shanghai.aliyuncs.com/jwh/sql_platform:xxx .
docker run --name sql_platform -p 80:8000 -e PYTHONENV=stage  -d registry.cn-shanghai.aliyuncs.com/jwh/sql_platform:xxx
docker save  d8095bd21edf -o sql_platform.tar
docker load --input sql_platform.tar

docker run --name goinception -p 4000:4000 -e TZ=Asia/Shanghai -v /data/goinception/config.toml:/etc/config.toml   -d  hanchuanchuan/goinception
