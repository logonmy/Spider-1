
## 临时存放redis数据

drop table if exists spider.redis_mobile2name_and_email_final
;

create table if not exists spider.redis_mobile2name_and_email_final
(
id bigint auto_increment primary key,
mobile varchar(1000) null,
name_and_email varchar(1000) null
)
;