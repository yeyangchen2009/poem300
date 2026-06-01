{{ config(materialized='table') }}

-- ODS: 任命类型代码表，定义任命方式的分类
-- 源表: APPOINTMENT_TYPES（6280 行）

SELECT
    c_appt_type_code,  -- 任命类型编码
    c_appt_type_desc,  -- 任命类型英文描述
    c_appt_type_desc_chn,  -- 任命类型中文描述
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'APPOINTMENT_TYPES') }}
