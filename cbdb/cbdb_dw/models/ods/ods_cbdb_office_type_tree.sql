{{ config(materialized='table') }}

-- ODS: 存储官职类型分类的层次结构信息，支持树状结构展示官职类型的继承关系
-- 源表: OFFICE_TYPE_TREE（109214 行）

SELECT
    c_office_type_node_id,  -- 官职类型节点的唯一标识符
    c_office_type_desc,  -- 官职类型的英文描述
    c_office_type_desc_chn,  -- 官职类型的中文描述
    c_parent_id,  -- 父级节点的唯一标识符，用于构建层级关系
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'OFFICE_TYPE_TREE') }}
