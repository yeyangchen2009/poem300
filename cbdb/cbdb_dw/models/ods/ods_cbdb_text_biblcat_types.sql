{{ config(materialized='table') }}

-- ODS: 存储文本书目分类类型的层级结构信息，用于管理不同分类类型的父子关系和展示顺序。
-- 源表: TEXT_BIBLCAT_TYPES（138229 行）

SELECT
    c_text_cat_type_id,  -- 分类类型的唯一标识符
    c_text_cat_type_desc,  -- 分类类型的英文描述
    c_text_cat_type_desc_chn,  -- 分类类型的中文描述
    c_text_cat_type_parent_id,  -- 父级分类类型的ID，用于构建层级结构
    c_text_cat_type_level,  -- 分类类型在层级结构中的等级（如：1级为顶层分类）
    c_text_cat_type_sortorder,  -- 同一层级内分类类型的展示顺序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_BIBLCAT_TYPES') }}
