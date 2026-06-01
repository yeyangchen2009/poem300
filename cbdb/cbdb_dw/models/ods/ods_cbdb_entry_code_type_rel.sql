{{ config(materialized='table') }}

-- ODS: 条目代码与类型关联表，用于定义每个条目代码对应的条目类型
-- 源表: ENTRY_CODE_TYPE_REL（87242 行）

SELECT
    c_entry_code,  -- 条目代码，关联到ENTRY_CODES表的c_entry_code字段
    c_entry_type,  -- 条目类型，关联到ENTRY_TYPES表的c_entry_type字段
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ENTRY_CODE_TYPE_REL') }}
