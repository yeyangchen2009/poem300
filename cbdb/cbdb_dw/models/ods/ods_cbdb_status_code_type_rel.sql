{{ config(materialized='table') }}

-- ODS: 状态代码与状态类型代码关联表，用于映射状态代码与其对应的状态类型分类关系
-- 源表: STATUS_CODE_TYPE_REL（136751 行）

SELECT
    c_status_code,  -- 状态代码，关联到STATUS_CODES表的c_status_code字段
    c_status_type_code,  -- 状态类型代码，关联到STATUS_TYPES表的c_status_type_code字段
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'STATUS_CODE_TYPE_REL') }}
