{{ config(materialized='table') }}

-- ODS: 存储官员任职方式类型的编码表，用于标识官员获得职位的方式（如任命、选举、继承等）
-- 源表: ASSUME_OFFICE_CODES（15207 行）

SELECT
    c_assume_office_code,  -- 担任职务方式的唯一标识代码
    c_assume_office_desc_chn,  -- 任职方式的中文描述（如'任命'、'世袭'等）
    c_assume_office_desc,  -- 任职方式的英文描述（如'Appointment'、'Hereditary'等）
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ASSUME_OFFICE_CODES') }}
