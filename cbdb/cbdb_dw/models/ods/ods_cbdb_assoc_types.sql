{{ config(materialized='table') }}

-- ODS: 存储关联类型的主分类表，定义社会关系类型的层级结构和展示顺序
-- 源表: ASSOC_TYPES（15204 行）

SELECT
    c_assoc_type_code,  -- 关联类型唯一标识符，用于区分不同类型的社会关系分类
    c_assoc_type_desc,  -- 关联类型的英文描述，说明该分类的具体含义
    c_assoc_type_desc_chn,  -- 关联类型的中文描述，说明该分类的具体含义
    c_assoc_type_parent_id,  -- 父级关联类型ID，用于构建多层级分类结构
    c_assoc_type_level,  -- 分类层级编号，表示该类型在树形结构中的位置（如1级为根分类）
    c_assoc_type_sortorder,  -- 分类排序序号，控制同层级分类的显示顺序
    c_assoc_type_short_desc,  -- 关联类型简短描述，用于界面显示等需要简洁说明的场景
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ASSOC_TYPES') }}
