{{ config(materialized='table') }}

-- ODS: 记录人物传记资料的主要来源信息，包括引用文本、页码和来源类型标记
-- 源表: BIOG_SOURCE_DATA（56237 行）

SELECT
    c_personid,  -- 人物唯一标识符，关联BIOG_MAIN表的c_personid
    c_textid,  -- 文献唯一标识符，关联TEXT_CODES表的c_textid
    c_pages,  -- 文献中具体引用页码或章节信息
    c_notes,  -- 关于资料来源的补充说明或注释
    c_main_source,  -- 标记是否为主要传记来源（1=是，0=否）
    c_self_bio,  -- 标记是否为自传类文本（1=是，0=否）
    c_created_by,  -- 记录创建人
    c_created_date,  -- 记录创建时间
    c_modified_by,  -- 记录修改人
    c_modified_date,  -- 记录修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_SOURCE_DATA') }}
