{{ config(materialized='table') }}

-- ODS: 行政区类别与类型的关联关系表
-- 源表: ADMIN_CAT_CODE_TYPE_REL（1180 行）

SELECT
    c_admin_cat_code,  -- 行政区类别编码
    c_admin_cat_type_code,  -- 行政区类型编码
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ADMIN_CAT_CODE_TYPE_REL') }}
