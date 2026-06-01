{{ config(materialized='table') }}

-- ODS: 任命方式代码表，定义官员任命的具体方式
-- 源表: APPOINTMENT_CODES（6272 行）

SELECT
    c_appt_code,  -- 任命方式编码
    c_appt_desc_chn,  -- 任命方式中文描述
    c_appt_desc,  -- 任命方式英文描述
    c_appt_desc_chn_alt,  -- 任命方式中文别名
    c_appt_desc_alt,  -- 任命方式英文别名
    c_notes,  -- 备注说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'APPOINTMENT_CODES') }}
