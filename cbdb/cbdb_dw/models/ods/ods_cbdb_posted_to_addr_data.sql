{{ config(materialized='table') }}

-- ODS: 记录人物职务派遣地点关联信息表，存储官员被派往具体地理位置的任职记录
-- 源表: POSTED_TO_ADDR_DATA（109282 行）

SELECT
    c_posting_id,  -- 职务派遣记录的唯一标识符，关联POSTED_TO_OFFICE_DATA表的派遣记录
    c_personid,  -- 人物唯一标识符，关联BIOG_MAIN表的c_personid字段
    c_office_id,  -- 官职机构唯一标识符，关联OFFICE_CODES表的c_office_id字段
    c_addr_id,  -- 地理地址唯一标识符，关联ADDRESSES表的c_addr_id字段
    c_created_by,  -- 记录创建人
    c_created_date,  -- 记录创建时间
    c_modified_by,  -- 记录修改人
    c_modified_date,  -- 记录修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSTED_TO_ADDR_DATA') }}
