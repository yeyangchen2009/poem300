{{ config(materialized='table') }}

-- ODS: 记录人物官职任职信息，包含任职时间、官职ID、任命类型、任职机构、来源文献等信息
-- 源表: POSTED_TO_OFFICE_DATA（114545 行）

SELECT
    c_personid,  -- 人物ID，关联BIOG_MAIN表的c_personid
    c_office_id,  -- 官职ID，关联OFFICE_CODES表的c_office_id
    c_posting_id,  -- 任职记录唯一标识符
    c_sequence,  -- 任职顺序编号
    c_firstyear,  -- 任职起始年份（公历年）
    c_fy_nh_code,  -- 起始年份对应的年号编码，关联NIAN_HAO表的c_nianhao_id
    c_fy_nh_year,  -- 起始年份在年号纪年中的具体年份
    c_fy_range,  -- 起始年份范围编码，关联YEAR_RANGE_CODES表的c_range_code
    c_lastyear,  -- 任职结束年份（公历年）
    c_ly_nh_code,  -- 结束年份对应的年号编码，关联NIAN_HAO表的c_nianhao_id
    c_ly_nh_year,  -- 结束年份在年号纪年中的具体年份
    c_ly_range,  -- 结束年份范围编码，关联YEAR_RANGE_CODES表的c_range_code
    c_appt_code,  -- 任命方式编码
    c_assume_office_code,  -- 到任方式编码，关联ASSUME_OFFICE_CODES表的c_assume_office_code
    c_inst_code,  -- 机构代码，关联SOCIAL_INSTITUTION_CODES表的c_inst_code
    c_inst_name_code,  -- 机构名称代码，关联SOCIAL_INSTITUTION_NAME_CODES表的c_inst_name_code
    c_source,  -- 来源文献ID，关联TEXT_CODES表的c_textid
    c_pages,  -- 来源文献页码或卷册信息
    c_notes,  -- 备注信息
    c_office_id_backup,  -- 旧版官职ID备份字段
    c_office_category_id,  -- 官职分类ID，关联OFFICE_CATEGORIES表的c_office_category_id
    c_fy_intercalary,  -- 起始年份是否闰月（0=否，1=是）
    c_fy_month,  -- 起始月份（1-12）
    c_ly_intercalary,  -- 结束年份是否闰月（0=否，1=是）
    c_ly_month,  -- 结束月份（1-12）
    c_fy_day,  -- 起始日（农历日）
    c_ly_day,  -- 结束日（农历日）
    c_fy_day_gz,  -- 起始日干支编码，关联GANZHI_CODES表的c_ganzhi_code
    c_ly_day_gz,  -- 结束日干支编码，关联GANZHI_CODES表的c_ganzhi_code
    c_dy,  -- 朝代编码，关联DYNASTIES表的c_dy
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSTED_TO_OFFICE_DATA') }}
