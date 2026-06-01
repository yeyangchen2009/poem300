{{ config(materialized='table') }}

-- ODS: 存储度量单位的代码及其描述信息，包括英文和中文名称。
-- 源表: MEASURE_CODES（107901 行）

SELECT
    c_measure_code,  -- 度量单位的唯一标识代码
    c_measure_desc,  -- 度量单位的英文描述或名称
    c_measure_desc_chn,  -- 度量单位的中文描述或名称
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'MEASURE_CODES') }}
