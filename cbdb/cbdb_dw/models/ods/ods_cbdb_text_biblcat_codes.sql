{{ config(materialized='table') }}

-- ODS: 存储文本目录分类代码及其层级结构的元数据表，用于定义文献目录的分类体系（如四部分类法扩展体系）。包含分类代码、描述、中文名称、拼音、父级分类ID、分类层级和排序顺序等字段。
-- 源表: TEXT_BIBLCAT_CODES（138222 行）

SELECT
    c_text_cat_code,  -- 分类代码唯一标识符，作为分类体系节点的唯一编码
    c_text_cat_desc,  -- 分类的英文描述，说明该分类的具体内容（如'Historiography'表示史部）
    c_text_cat_desc_chn,  -- 分类的中文名称（如'史部'），用于显示和检索
    c_text_cat_pinyin,  -- 分类中文名称的拼音形式，用于音序排序和检索（如'shibu'）
    c_text_cat_parent_id,  -- 父级分类代码，指向同一表中c_text_cat_code字段，用于构建树形层级结构（如'史部'的父节点为根节点）
    c_text_cat_level,  -- 分类在树形结构中的层级（如1表示一级分类，2表示二级子分类）
    c_text_cat_sortorder,  -- 分类在同一层级中的显示顺序编号，用于控制目录展示次序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_BIBLCAT_CODES') }}
