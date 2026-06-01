{{ config(materialized='table') }}

-- ODS: 存储与人物相关的事件记录数据，包括事件类型、时间、地点、角色及来源信息
-- 源表: EVENTS_DATA（94529 行）

SELECT
    c_personid,  -- 关联到 BIOG_MAIN 表的人物唯一标识符
    c_sequence,  -- 同一事件记录中的排序序号
    c_event_code,  -- 关联到 EVENT_CODES 表的事件类型代码
    c_role,  -- 人物在事件中的角色或职务描述
    c_year,  -- 事件发生的公历年份
    c_nh_code,  -- 关联到 NIAN_HAO 表的年号代码
    c_nh_year,  -- 年号纪年中的年份
    c_yr_range,  -- 关联到 YEAR_RANGE_CODES 表的年份范围代码
    c_intercalary,  -- 标记是否为闰月（0-否，1-是）
    c_month,  -- 事件发生的月份（农历）
    c_day,  -- 事件发生的日期（农历）
    c_day_ganzhi,  -- 关联到 GANZHI_CODES 表的干支日代码
    c_addr_id,  -- 关联到 ADDR_CODES 表的事件发生地地址代码
    c_source,  -- 关联到 TEXT_CODES 表的来源文本代码
    c_pages,  -- 来源文本中的具体页码或位置
    c_event,  -- 事件内容的自由文本描述
    c_notes,  -- 事件相关备注或补充说明
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'EVENTS_DATA') }}
