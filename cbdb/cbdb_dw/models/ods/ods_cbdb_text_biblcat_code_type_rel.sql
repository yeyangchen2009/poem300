{{ config(materialized='table') }}

-- ODS: 存储文献目录分类代码与其对应分类类型之间的关联关系
-- 源表: TEXT_BIBLCAT_CODE_TYPE_REL（138227 行）

SELECT
    c_text_cat_code,  -- 文献目录分类代码标识符，关联到TEXT_BIBLCAT_CODES表的c_text_cat_code字段
    c_text_cat_type_id,  -- 文献目录分类类型标识符，关联到TEXT_BIBLCAT_TYPES表的c_text_cat_type_id字段
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_BIBLCAT_CODE_TYPE_REL') }}
