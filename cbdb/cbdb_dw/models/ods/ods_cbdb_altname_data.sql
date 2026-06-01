{{ config(materialized='table') }}

-- ODS: 存储人物别名信息数据表，记录历史人物的各种别名、字号、谥号等替代名称信息
-- 源表: ALTNAME_DATA（1186 行）

SELECT
    c_personid,  -- 关联人物主键，对应BIOG_MAIN表的c_personid
    c_alt_name,  -- 人物非中文别名/字号（如罗马化名称）
    c_alt_name_chn,  -- 人物中文别名/字号（汉字形式）
    c_alt_name_type_code,  -- 别名类型代码，关联ALTNAME_CODES表的c_name_type_code
    c_sequence,  -- 别名显示顺序编号
    c_source,  -- 资料来源标识，关联TEXT_CODES表的c_textid
    c_pages,  -- 资料来源页码或卷号
    c_notes,  -- 别名备注说明
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建时间
    c_modified_date,  -- 记录最后修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ALTNAME_DATA') }}
