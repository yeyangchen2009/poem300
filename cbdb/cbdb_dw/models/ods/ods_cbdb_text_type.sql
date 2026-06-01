{{ config(materialized='table') }}

-- ODS: 存储文本类型分类信息，用于定义不同文本类型及其层次结构
-- 源表: TEXT_TYPE（140598 行）

SELECT
    c_text_type_code,  -- 文本类型唯一标识代码
    c_text_type_desc,  -- 文本类型英文描述
    c_text_type_desc_chn,  -- 文本类型中文描述
    c_text_type_parent_id,  -- 父级文本类型代码，用于构建分类层级
    c_text_type_level,  -- 当前类型在分类树中的层级
    c_text_type_sortorder,  -- 同层级类型显示顺序编号
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_TYPE') }}
