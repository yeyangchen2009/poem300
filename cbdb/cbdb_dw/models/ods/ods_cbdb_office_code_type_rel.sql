{{ config(materialized='table') }}

-- ODS: 存储官职代码与官职类型树节点之间的关联关系，用于建立官职与其分类体系之间的对应关系
-- 源表: OFFICE_CODE_TYPE_REL（108833 行）

SELECT
    c_office_id,  -- 关联的官职唯一标识符，对应OFFICE_CODES表的c_office_id字段
    c_office_tree_id,  -- 关联的官职类型树节点ID，对应OFFICE_TYPE_TREE表的c_office_type_node_id字段
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'OFFICE_CODE_TYPE_REL') }}
