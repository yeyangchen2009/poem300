{{ config(materialized='table') }}

-- ODS: 存储不同入仕途径类型的分类层级结构，用于定义科举考试、荫补等不同入仕途径的树状分类体系
-- 源表: ENTRY_TYPES（94505 行）

SELECT
    c_entry_type,  -- 条目类型唯一标识符代码
    c_entry_type_desc,  -- 条目类型的英文描述（如科举考试、恩荫等）
    c_entry_type_desc_chn,  -- 条目类型的中文描述
    c_entry_type_parent_id,  -- 父级条目类型ID，用于构建分类层级结构
    c_entry_type_level,  -- 分类层级深度（如1级分类、2级子类等）
    c_entry_type_sortorder,  -- 同层级分类的显示排序序号
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ENTRY_TYPES') }}
