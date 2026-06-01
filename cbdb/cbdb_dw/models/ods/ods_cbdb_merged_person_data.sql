{{ config(materialized='table') }}

-- ODS: 人物合并记录表，记录已合并的重复人物ID
-- 源表: MERGED_PERSON_DATA（107903 行）

SELECT
    c_personid,  -- 合并后保留的人物ID
    c_merged_from_personid,  -- 被合并的原始人物ID
    c_notes,  -- 备注说明
    c_source,  -- 资料来源ID
    c_pages,  -- 资料页码
    c_created_by,  -- 记录创建人
    c_modified_by,  -- 记录修改人
    c_created_date,  -- 记录创建时间
    c_modified_date,  -- 记录修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'MERGED_PERSON_DATA') }}
