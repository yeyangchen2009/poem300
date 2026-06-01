{{ config(materialized='table') }}

-- ODS: 存储人物关联关系的类型代码及其描述信息，用于定义不同人物间的关联类型和角色关系。
-- 源表: ASSOC_CODES（6282 行）

SELECT
    c_assoc_code,  -- 关联类型的唯一标识符代码，用于唯一标识一种关联关系类型。
    c_assoc_pair,  -- 关联关系中的第一个角色类型代码，可能与其他代码表关联。
    c_assoc_pair2,  -- 关联关系中的第二个角色类型代码，可能与其他代码表关联。
    c_assoc_desc,  -- 关联关系的英文描述，说明该代码对应的具体关联类型。
    c_assoc_desc_chn,  -- 关联关系的中文描述，说明该代码对应的具体关联类型。
    c_assoc_role_type,  -- 关联角色类型的分类代码，例如主动或被动角色（如 'A' 表示主动）。
    c_sortorder,  -- 排序序号，用于控制该关联类型在列表中的显示顺序。
    c_example,  -- 关联类型的示例说明，提供具体应用场景的示例文本。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ASSOC_CODES') }}
