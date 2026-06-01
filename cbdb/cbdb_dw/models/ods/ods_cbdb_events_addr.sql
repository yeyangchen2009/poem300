{{ config(materialized='table') }}

-- ODS: 存储事件与地址关联信息，记录事件发生地点的时空信息
-- 源表: EVENTS_ADDR（94527 行）

SELECT
    c_event_code,  -- 事件编码
    c_personid,  -- 人物唯一标识符，关联BIOG_MAIN表的c_personid
    c_sequence,  -- 事件序号
    c_addr_id,  -- 地址唯一标识符，关联ADDR_CODES表的c_addr_id
    c_year,  -- 事件发生的年份（公历）
    c_nh_code,  -- 年号代码，关联NIAN_HAO表的c_nianhao_id
    c_nh_year,  -- 年号纪年中的年份
    c_yr_range,  -- 年份范围代码，关联YEAR_RANGE_CODES表的c_range_code
    c_intercalary,  -- 闰月标识（0=非闰月，1=闰月）
    c_month,  -- 事件发生的月份（农历）
    c_day,  -- 事件发生的日期（农历）
    c_day_ganzhi,  -- 干支日代码，关联GANZHI_CODES表的c_ganzhi_code
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'EVENTS_ADDR') }}
