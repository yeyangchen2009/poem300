{{ config(materialized='table') }}

-- ODS: 存储官职分类信息，包括中英文分类描述和备注信息
-- 源表: OFFICE_CATEGORIES（107997 行）

SELECT
    c_office_category_id,  -- 官职分类唯一标识符
    c_category_desc,  -- 官职分类英文描述
    c_category_desc_chn,  -- 官职分类中文描述
    c_notes,  -- 分类备注信息
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'OFFICE_CATEGORIES') }}
