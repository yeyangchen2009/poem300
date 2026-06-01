{{ config(materialized='table') }}

-- ODS: 存储中国历代朝代的基本信息，包括朝代的中英文名称、起止年份及排序顺序
-- 源表: DYNASTIES（87233 行）

SELECT
    c_dy,  -- 朝代唯一ID
    c_dynasty,  -- 朝代名称（英文）
    c_dynasty_chn,  -- 朝代名称（中文）
    c_start,  -- 朝代起始年份（公元纪年）
    c_end,  -- 朝代结束年份（公元纪年）
    c_sort,  -- 排序序号，用于确定朝代在列表中的显示顺序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'DYNASTIES') }}
