{{ config(materialized='table') }}

-- ODS: 存储父母状态代码及其描述，用于标识人物父母在世状态及相关情况
-- 源表: PARENTAL_STATUS_CODES（109271 行）

SELECT
    c_parental_status_code,  -- 父母状态唯一标识代码，用于关联其他表中涉及父母状态的数据
    c_parental_status_desc,  -- 父母状态英文描述（如：'Both parents alive'）
    c_parental_status_desc_chn,  -- 父母状态中文描述（如：'父母俱存'）
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'PARENTAL_STATUS_CODES') }}
