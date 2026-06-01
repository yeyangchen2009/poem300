{{ config(materialized='table') }}

-- ODS: 社会机构别名数据表，存储机构的其他名称或别名信息
-- 源表: SOCIAL_INSTITUTION_ALTNAME_DATA（136591 行）

SELECT
    c_inst_name_code,  -- 机构名称代码，外键关联SOCIAL_INSTITUTION_NAME_CODES表的c_inst_name_code字段
    c_inst_code,  -- 机构代码，外键关联SOCIAL_INSTITUTION_CODES表的c_inst_code字段
    c_inst_altname_type,  -- 别名类型代码，外键关联SOCIAL_INSTITUTION_ALTNAME_CODES表的c_inst_altname_type字段
    c_inst_altname_hz,  -- 机构别名汉字表示
    c_inst_altname_py,  -- 机构别名拼音表示
    c_source,  -- 资料来源，外键关联TEXT_CODES表的c_textid字段
    c_pages,  -- 资料来源页码或位置信息
    c_notes,  -- 备注或附加说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_ALTNAME_DATA') }}
