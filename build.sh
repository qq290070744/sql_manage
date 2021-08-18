tag=20210817
docker build -t registry.cn-shanghai.aliyuncs.com/jwh/sql_platform:$tag .
docker push registry.cn-shanghai.aliyuncs.com/jwh/sql_platform:$tag
echo $tag
