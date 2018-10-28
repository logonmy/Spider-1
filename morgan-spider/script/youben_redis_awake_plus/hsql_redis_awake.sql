set hive.execution.engine=tez;
set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;
set hive.exec.max.dynamic.partitions.pernode = 1000;
set hive.exec.max.dynamic.partitions=1000;

--stg.youben_redis_awake_temp
drop table if exists stg.youben_redis_awake_temp;

create table if not exists stg.youben_redis_awake_temp(
	key1 string,
	key2 string,
	mobile string
);

insert into stg.youben_redis_awake_temp
select key1,concat(companies,'|',schools) as key2,mobile
from
(
    select mobile,key1,companies,concat_ws('#',collect_set(school)) as schools
    from
    (
        select distinct mobile,key1,companies,trim(school) as school
        from
        (
        select
          mobile,key1,companies,school
        from
        (
            select mobile,key1,concat_ws('#',collect_set(company)) as companies,schools
            from
            (
                select distinct
                    mobile,key1,
                    trim(regexp_replace(t30.company,'\\(.*?\\)|(科技有限|有限责任|有限|分||科技集团有限|集团有限)?公司.*?$','')) as company,
                    schools
                from
                (
                    select
                    mobile,key1,company,schools
                    from
                    (
                        select distinct
                        externalid as mobile,
                        concat(
                          firstletter,birthyear,gender,
                          case when currentprovincecode in (8611,8612,8631,8650)
                          then currentprovincecode else currentcitycode end
                        ) as key1,
                        regexp_replace(regexp_replace(regexp_replace(lower(companies),'[ #|*？?]+',''),'[（]+','('),'[）]+',')')
                        as companies,
                        regexp_replace(schools,'[#|]+','') as schools
                        from stg.s_resume_normal_search_temp
                        where
                        firstletter is not null and firstletter rlike '[\\u4e00-\\u9fa5]'
                        and birthyear is not null and length(birthyear) = 4
                        and gender is not null and length(gender) = 1
                        and companies is not null and trim(companies) != '' and length(companies) < 200
                        and schools is not null and trim(schools) != '' and length(schools) < 200
                        and (currentprovincecode in (8611,8612,8631,8650)
                        or currentcitycode is not null)
                    )as t2
                    lateral view explode(split(companies, ',')) companies as company
                )as t30
                where length(trim(regexp_replace(t30.company,'\\(.*?\\)|(科技有限|有限责任|有限|分||科技集团有限|集团有限)?公司.*?$','')))<40
            ) as t31
            group by mobile,key1,schools
        ) as t3
        lateral view explode(split(schools, ',')) schools as school
        ) as t4
        where length(trim(school)) < 40
    ) as t5
    group by mobile,key1,companies
) as t6
;

--default.youben_redis_awake_final_temp
drop table if exists default.youben_redis_awake_final_temp;

create table if not exists default.youben_redis_awake_final_temp(
	id bigint,
	key1 string,
	key2 string,
	mobiles string
)
partitioned by (rand_ int);

insert overwrite table default.youben_redis_awake_final_temp partition(rand_)
select
row_number() over() + t3.max_id as id,
t1.key1,
t1.key2,
t1.mobiles,
t1.rand_
from
(
  select a.key1,a.key2,a.mobile as mobiles ,int(20*rand()) as rand_
  from stg.youben_redis_awake_temp a
)as t1
cross join
(
    select coalesce(max(id),0) max_id from default.youben_redis_awake_final_temp
) t3;