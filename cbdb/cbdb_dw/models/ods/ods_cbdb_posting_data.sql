{{ config(materialized='table') }}

-- ODS: 存储任职记录的基本关联信息，用于关联人物与其任职记录的主表
-- 源表: POSTING_DATA（131754 行）

SELECT
    c_personid,  -- 关联人物的唯一标识符，对应 BIOG_MAIN 表中的 c_personid
    c_posting_id,  -- 任职记录的唯一标识符（必填字段），可关联到 POSTED_TO_OFFICE_DATA 或 POSTED_TO_ADDR_DATA 表的 c_posting_id
    c_created_by,  -- 记录创建人
    c_created_date,  -- 记录创建时间
    c_modified_by,  -- 记录修改人
    c_modified_date,  -- 记录修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSTING_DATA') }}
