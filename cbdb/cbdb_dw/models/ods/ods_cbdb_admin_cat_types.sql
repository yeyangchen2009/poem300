{{ config(materialized='table') }}

-- ODS: 行政区类型代码表，定义行政区划类型分类
-- 源表: ADMIN_CAT_TYPES（1182 行）

SELECT
    c_admin_cat_type_code,  -- 行政区类型编码
    c_admin_cat_type_hz,  -- 行政区类型中文名
    c_admin_cat_type_trans,  -- 行政区类型英文名
    c_notes,  -- 备注说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ADMIN_CAT_TYPES') }}
