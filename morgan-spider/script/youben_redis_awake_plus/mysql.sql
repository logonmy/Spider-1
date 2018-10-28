drop table if exists spider.youben_redis_awake_final_temp
;

create table if not exists spider.youben_redis_awake_final_temp
(
id bigint auto_increment primary key,
key1 varchar(1000) null,
key2 varchar(1000) null,
mobiles mediumtext null
)
;