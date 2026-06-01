{{ config(materialized='table') }}

-- ODS: 行政区类别代码表，定义行政区划的类型编码
-- 源表: ADMIN_CAT_CODES（1175 行）

SELECT
    c_admin_cat_code,  -- 行政区类别编码
    c_admin_cat_py,  -- 行政区类别拼音名
    c_admin_cat_hz,  -- 行政区类别中文名
    c_admin_cat_trans,  -- 行政区类别英文名
    c_notes,  -- 备注说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ADMIN_CAT_CODES') }}
