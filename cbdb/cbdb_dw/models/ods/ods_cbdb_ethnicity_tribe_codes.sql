{{ config(materialized='table') }}

-- ODS: 存储中国历史上民族、族群及其子群的分类代码信息，包含民族名称、法律分类、罗马化拼写、姓氏、备注及在历代史书中的记载引用。
-- 源表: ETHNICITY_TRIBE_CODES（94507 行）

SELECT
    c_ethnicity_code,  -- 主民族代码，唯一标识特定民族或族群分类
    c_group_code,  -- 所属上级族群代码，用于层级分类
    c_subgroup_code,  -- 子群细分代码，标识更具体的族群分支
    c_altname_code,  -- 替代名称或别名代码，关联其他名称编码表
    c_name_chn,  -- 民族或族群的中文名称
    c_name,  -- 民族或族群的英文或罗马化名称
    c_ethno_legal_cat,  -- 民族法律分类（如官方认定的族群类别）
    c_romanized,  -- 民族名称的罗马化拼写标准（如拼音或威妥玛式）
    c_surname,  -- 该民族常见的姓氏
    c_notes,  -- 备注或附加说明
    c_sortorder,  -- 排序序号，用于控制数据展示顺序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ETHNICITY_TRIBE_CODES') }}
