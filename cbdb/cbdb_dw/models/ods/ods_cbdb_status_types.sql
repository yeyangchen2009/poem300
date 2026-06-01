{{ config(materialized='table') }}

-- ODS: 存储状态类型层级结构的元数据表，用于定义不同社会身份状态类型的分类及其层级关系
-- 源表: STATUS_TYPES（138220 行）

SELECT
    c_status_type_code,  -- 状态类型唯一标识代码，12位定长字符类型
    c_status_type_desc,  -- 状态类型的英文描述，可变长度说明文本
    c_status_type_chn,  -- 状态类型的中文描述，包含汉字说明
    c_status_type_parent_code,  -- 父级状态类型代码，用于构建多级分类结构
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'STATUS_TYPES') }}
