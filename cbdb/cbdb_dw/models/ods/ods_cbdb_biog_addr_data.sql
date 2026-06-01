{{ config(materialized='table') }}

-- ODS: 存储人物生平地址关联数据，记录人物在不同时间段内的地址信息及其类型、来源和日期细节
-- 源表: BIOG_ADDR_DATA（15211 行）

SELECT
    c_personid,  -- 关联BIOG_MAIN表的人物唯一标识符
    c_addr_id,  -- 关联ADDRESSES表的地址唯一标识符
    c_addr_type,  -- 地址类型代码，关联BIOG_ADDR_CODES表的c_addr_type字段
    c_sequence,  -- 地址信息在人物生平中的排序序列号
    c_firstyear,  -- 地址关联起始年份（公历年）
    c_lastyear,  -- 地址关联结束年份（公历年）
    c_source,  -- 资料来源代码，关联TEXT_CODES表的c_textid字段
    c_pages,  -- 资料来源页码或卷册信息
    c_notes,  -- 地址关联备注信息
    c_fy_nh_code,  -- 起始年份对应的年号代码，关联NIAN_HAO表的c_nianhao_id
    c_ly_nh_code,  -- 结束年份对应的年号代码，关联NIAN_HAO表的c_nianhao_id
    c_fy_nh_year,  -- 起始年份对应的年号纪年
    c_ly_nh_year,  -- 结束年份对应的年号纪年
    c_fy_range,  -- 起始年份范围代码，关联YEAR_RANGE_CODES表的c_range_code
    c_ly_range,  -- 结束年份范围代码，关联YEAR_RANGE_CODES表的c_range_code
    c_natal,  -- 标识是否为籍贯地址（1=是，0=否）
    c_fy_intercalary,  -- 起始年份是否包含闰月（1=是，0=否）
    c_ly_intercalary,  -- 结束年份是否包含闰月（1=是，0=否）
    c_fy_month,  -- 起始月份（农历）
    c_ly_month,  -- 结束月份（农历）
    c_fy_day,  -- 起始日期（农历）
    c_ly_day,  -- 结束日期（农历）
    c_fy_day_gz,  -- 起始日期的干支代码，关联GANZHI_CODES表的c_ganzhi_code
    c_ly_day_gz,  -- 结束日期的干支代码，关联GANZHI_CODES表的c_ganzhi_code
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_delete,  -- 软删除标记（1=已删除，0=未删除）
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_ADDR_DATA') }}
