{{ config(materialized='table') }}

-- ODS: 存储社会机构的基本信息，包括机构名称代码、机构代码、类型代码、起始与结束时间、年号关联、来源及注释等信息。
-- 源表: SOCIAL_INSTITUTION_CODES（136592 行）

SELECT
    c_inst_name_code,  -- 机构名称代码，对应 SOCIAL_INSTITUTION_NAME_CODES 表中的 c_inst_name_code 字段。
    c_inst_code,  -- 机构唯一标识代码，可能与 SOCIAL_INSTITUTION_CODES_CONVERSION 表关联。
    c_inst_type_code,  -- 机构类型代码，对应 SOCIAL_INSTITUTION_TYPES 表中的 c_inst_type_code 字段。
    c_inst_begin_year,  -- 机构的起始年份（公元纪年）。
    c_by_nianhao_code,  -- 起始年份对应的年号代码，关联 NIAN_HAO 表中的 c_nianhao_id。
    c_by_nianhao_year,  -- 年号对应的具体年份（如“洪武三年”中的“三年”）。
    c_by_year_range,  -- 起始年份的范围代码（如模糊年份），关联 YEAR_RANGE_CODES 表的 c_range_code。
    c_inst_begin_dy,  -- 机构起始朝代代码，关联 DYNASTIES 表的 c_dy 字段。
    c_inst_floruit_dy,  -- 机构活跃的主要朝代代码，关联 DYNASTIES 表的 c_dy 字段。
    c_inst_first_known_year,  -- 机构首次被记载的年份（公元纪年）。
    c_inst_end_year,  -- 机构的结束年份（公元纪年）。
    c_ey_nianhao_code,  -- 结束年份对应的年号代码，关联 NIAN_HAO 表中的 c_nianhao_id。
    c_ey_nianhao_year,  -- 结束年号对应的具体年份。
    c_ey_year_range,  -- 结束年份的范围代码，关联 YEAR_RANGE_CODES 表的 c_range_code。
    c_inst_end_dy,  -- 机构结束的朝代代码，关联 DYNASTIES 表的 c_dy 字段。
    c_inst_last_known_year,  -- 机构最后被记载的年份（公元纪年）。
    c_source,  -- 资料来源代码，关联 TEXT_CODES 表的 c_textid 字段。
    c_pages,  -- 资料来源中的具体页码或卷号。
    c_notes,  -- 关于该机构的其他注释或补充说明。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_CODES') }}
