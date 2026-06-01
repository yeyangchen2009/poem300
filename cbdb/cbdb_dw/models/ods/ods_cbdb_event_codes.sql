{{ config(materialized='table') }}

-- ODS: 存储事件类型代码及其相关信息，包括事件名称、时间范围、关联地址、朝代和来源信息。
-- 源表: EVENT_CODES（94549 行）

SELECT
    c_event_code,  -- 事件类型的唯一标识代码
    c_event_name_chn,  -- 事件类型的中文名称
    c_event_name,  -- 事件类型的英文名称
    c_fy_yr,  -- 事件开始的公历年份
    c_ly_yr,  -- 事件结束的公历年份
    c_fy_nh_code,  -- 事件开始的年号代码（关联NIAN_HAO表的c_nianhao_id）
    c_ly_nh_code,  -- 事件结束的年号代码（关联NIAN_HAO表的c_nianhao_id）
    c_fy_nh_yr,  -- 事件开始的年号年份
    c_ly_nh_yr,  -- 事件结束的年号年份
    c_fy_intercalary,  -- 事件开始年份是否包含闰月（布尔值）
    c_fy_month,  -- 事件开始的月份（1-12）
    c_ly_intercalary,  -- 事件结束年份是否包含闰月（布尔值）
    c_ly_month,  -- 事件结束的月份（1-12）
    c_fy_range,  -- 事件开始年份的不确定性范围代码（关联YEAR_RANGE_CODES表的c_range_code）
    c_ly_range,  -- 事件结束年份的不确定性范围代码（关联YEAR_RANGE_CODES表的c_range_code）
    c_addr_id,  -- 关联地址的ID（关联ADDRESSES表的c_addr_id）
    c_dy,  -- 关联朝代的代码（关联DYNASTIES表的c_dy）
    c_source,  -- 来源文本的ID（关联TEXT_CODES表的c_textid）
    c_pages,  -- 来源文本中相关页码或章节
    c_event_notes,  -- 事件相关的附加注释或说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'EVENT_CODES') }}
