{{ config(materialized='table') }}

-- ODS: 存储现存状态代码及其对应的中英文描述，用于标识文献或作品的现存状态（如现存、缺失等）。
-- 源表: EXTANT_CODES（94553 行）

SELECT
    c_extant_code,  -- 现存状态唯一标识代码（整数类型）。
    c_extant_desc,  -- 现存状态的英文描述（如 'Extant', 'Partially Lost'）。
    c_extant_desc_chn,  -- 现存状态的中文描述（如 '现存', '部分缺失'）。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'EXTANT_CODES') }}
