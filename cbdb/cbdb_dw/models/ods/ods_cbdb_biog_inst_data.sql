{{ config(materialized='table') }}

-- ODS: 记录人物与社会机构关系的任职经历数据表
-- 源表: BIOG_INST_DATA（28060 行）

SELECT
    c_personid,  -- 人物唯一标识符，关联 BIOG_MAIN 表
    c_inst_name_code,  -- 机构名称代码，关联 SOCIAL_INSTITUTION_NAME_CODES 表
    c_inst_code,  -- 机构类型代码，关联 SOCIAL_INSTITUTION_CODES 表
    c_bi_role_code,  -- 人物在机构中的角色代码，关联 BIOG_INST_CODES 表
    c_bi_begin_year,  -- 任职开始年份（绝对年份）
    c_bi_by_nh_code,  -- 任职开始年号代码，关联 NIAN_HAO 表
    c_bi_by_nh_year,  -- 任职开始年号的年份
    c_bi_by_range,  -- 任职开始年份范围代码，关联 YEAR_RANGE_CODES 表
    c_bi_end_year,  -- 任职结束年份（绝对年份）
    c_bi_ey_nh_code,  -- 任职结束年号代码，关联 NIAN_HAO 表
    c_bi_ey_nh_year,  -- 任职结束年号的年份
    c_bi_ey_range,  -- 任职结束年份范围代码，关联 YEAR_RANGE_CODES 表
    c_source,  -- 资料来源标识符，关联 TEXT_CODES 表
    c_pages,  -- 资料来源页码或卷号
    c_notes,  -- 备注或补充说明
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_INST_DATA') }}
