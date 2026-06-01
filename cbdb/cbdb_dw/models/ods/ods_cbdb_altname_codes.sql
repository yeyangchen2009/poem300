{{ config(materialized='table') }}

-- ODS: 存储别名类型代码及其描述的表，包括中文和英文版本
-- 源表: ALTNAME_CODES（1184 行）

SELECT
    c_name_type_code,  -- 别名类型的唯一标识代码
    c_name_type_desc,  -- 别名类型的英文描述
    c_name_type_desc_chn,  -- 别名类型的中文描述
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ALTNAME_CODES') }}
