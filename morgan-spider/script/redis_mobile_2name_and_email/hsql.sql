SET hive.execution.engine = tez;
SET hive.exec.dynamic.partition = TRUE;
SET hive.exec.dynamic.partition.mode = nonstrict;
SET hive.exec.max.dynamic.partitions.pernode = 1000;
SET hive.exec.max.dynamic.partitions = 1000;

DROP TABLE IF EXISTS stg.redis_mobile2name_and_email;

CREATE TABLE IF NOT EXISTS stg.redis_mobile2name_and_email (
  mibile STRING,
  name_and_email STRING
);

INSERT INTO stg.redis_mobile2name_and_email
  SELECT
    t1.key,
    t1.value
  FROM (
         SELECT mobile AS KEY,
                          concat('"', NAME, '#', email,'"') AS VALUE,
                                                            row_number() OVER ( PARTITION BY mobile ORDER BY record_create_time DESC ) num
                                                                                                                                       FROM stg.s_resume_normal
                                                                                                                                       where not (name is null and email is null)
       ) AS t1
  WHERE t1.num = 1;


DROP TABLE IF EXISTS default.redis_mobile2name_and_email_final;

CREATE TABLE IF NOT EXISTS default.redis_mobile2name_and_email_final (
  id BIGINT,
  mibile STRING,
  name_and_email STRING
)partitioned BY (rand_ INT
);

INSERT overwrite TABLE DEFAULT.redis_mobile2name_and_email_final PARTITION (rand_)
SELECT
  row_number() over() + t3.max_id AS id,
  t1.mibile,
  t1.name_and_email,
  t1.rand_
FROM (
       SELECT
         mibile,
         name_and_email,
       INT (20*rand()) AS rand_
       FROM stg.redis_mobile2name_and_email
     ) AS t1
  CROSS JOIN
  (
    SELECT coalesce(max(id), 0) max_id
    FROM default.redis_mobile2name_and_email_final
  ) t3;