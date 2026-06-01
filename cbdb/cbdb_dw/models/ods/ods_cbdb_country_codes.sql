{{ config(materialized='table') }}

-- ODS: 存储国家代码及其对应的描述信息，包含中文和英文版本
-- 源表: COUNTRY_CODES（87231 行）

SELECT
    c_country_code,  -- 国家代码，唯一标识一个国家
    c_country_desc,  -- 国家名称的英文描述
    c_country_desc_chn,  -- 国家名称的中文描述
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'COUNTRY_CODES') }}
