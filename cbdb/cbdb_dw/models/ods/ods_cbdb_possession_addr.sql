{{ config(materialized='table') }}

-- ODS: 记录人物财产相关地址的关联表，用于将财产记录与地理位置信息进行关联
-- 源表: POSSESSION_ADDR（109275 行）

SELECT
    c_possession_record_id,  -- 财产记录唯一标识符，关联POSSESSION_DATA表的同名字段
    c_personid,  -- 人物唯一标识符，关联BIOG_MAIN表的c_personid字段
    c_addr_id,  -- 地址唯一标识符，关联ADDR_CODES表的c_addr_id字段
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSSESSION_ADDR') }}
