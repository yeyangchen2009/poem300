{{ config(materialized='table') }}

-- ODS: 存储关联关系代码与关联类型之间的映射关系，用于定义不同类型的社交关联对应的分类标识
-- 源表: ASSOC_CODE_TYPE_REL（6295 行）

SELECT
    c_assoc_code,  -- 关联关系代码，指向ASSOC_CODES表的c_assoc_code字段，标识具体的社交关系类型
    c_assoc_type_code,  -- 关联类型标识符，指向ASSOC_TYPES表，定义社交关系的分类层级
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ASSOC_CODE_TYPE_REL') }}
