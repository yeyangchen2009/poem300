{{ config(materialized='table') }}

-- ODS: 任命方式与类型的关联关系表
-- 源表: APPOINTMENT_CODE_TYPE_REL（6276 行）

SELECT
    c_appt_type_code,  -- 任命类型编码
    c_appt_code,  -- 任命方式编码
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'APPOINTMENT_CODE_TYPE_REL') }}
