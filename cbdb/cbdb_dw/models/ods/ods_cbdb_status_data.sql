{{ config(materialized='table') }}

-- ODS: 存储人物的状态信息，包括状态代码、起始年份、结束年份及相关补充信息
-- 源表: STATUS_DATA（136753 行）

SELECT
    c_personid,  -- 关联到BIOG_MAIN表的人物唯一标识符
    c_sequence,  -- 同一人物多个状态记录的排序序号
    c_status_code,  -- 状态代码，引用STATUS_CODES表的c_status_code
    c_firstyear,  -- 状态起始年份（公历年份）
    c_fy_nh_code,  -- 起始年份对应的年号代码，引用NIAN_HAO表的c_nianhao_id
    c_fy_nh_year,  -- 起始年份在年号中的具体年份
    c_fy_range,  -- 起始年份范围代码，引用YEAR_RANGE_CODES表的c_range_code
    c_lastyear,  -- 状态结束年份（公历年份）
    c_ly_nh_code,  -- 结束年份对应的年号代码，引用NIAN_HAO表的c_nianhao_id
    c_ly_nh_year,  -- 结束年份在年号中的具体年份
    c_ly_range,  -- 结束年份范围代码，引用YEAR_RANGE_CODES表的c_range_code
    c_supplement,  -- 状态补充说明（如特殊身份或头衔）
    c_source,  -- 资料来源代码，引用TEXT_CODES表的c_textid
    c_pages,  -- 资料来源的页码或卷号
    c_notes,  -- 状态记录的附加注释
    c_created_by,  -- 记录创建者标识
    c_modified_by,  -- 记录最后修改者标识
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'STATUS_DATA') }}
