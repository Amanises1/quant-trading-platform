启动数据库   
docker-compose   

进入数据库的docker容器   
docker exec -it postgres_for_quant psql -U quant -d quant_trading

查看所有数据表
\dt

查看某个表的信息
\d 'table_name'

查看某个表的数据
SELECT * FROM "table_name"
