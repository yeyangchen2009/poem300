{{ config(materialized='table') }}

-- ODS: 记录社会机构地址信息的关联表，包含机构地址类型、地理坐标及时间范围等信息
-- 源表: SOCIAL_INSTITUTION_ADDR（136468 行）

SELECT
    c_inst_name_code,  -- 社会机构名称代码，关联 SOCIAL_INSTITUTION_NAME_CODES 表的 c_inst_name_code
    c_inst_code,  -- 社会机构代码，关联 SOCIAL_INSTITUTION_CODES 表的 c_inst_code
    c_inst_addr_type_code,  -- 机构地址类型代码，关联 SOCIAL_INSTITUTION_ADDR_TYPES 表的 c_inst_addr_type_code
    c_inst_addr_begin_year,  -- 机构地址起始年份（可为空）
    c_inst_addr_end_year,  -- 机构地址结束年份（可为空）
    c_inst_addr_id,  -- 地址唯一标识符，关联 ADDR_CODES 表的 c_addr_id
    inst_xcoord,  -- 机构地址的经度坐标
    inst_ycoord,  -- 机构地址的纬度坐标
    c_source,  -- 资料来源标识符，关联 TEXT_CODES 表的 c_textid
    c_pages,  -- 资料引用页码或位置
    c_notes,  -- 附加说明或注释
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_ADDR') }}
