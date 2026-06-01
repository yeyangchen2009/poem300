{{ config(materialized='table') }}

-- ODS: 亲属丧服关系表，记录亲属关系的丧服等级和服属类型
-- 源表: KIN_MOURNING（107892 行）

SELECT
    c_kinrel,  -- 亲属关系英文名（主键）
    c_kinrel_alt,  -- 亲属关系英文别名
    c_kinrel_chn,  -- 亲属关系中文名
    c_mourning,  -- 丧服等级英文名
    c_mourning_chn,  -- 丧服等级中文名
    c_kindist,  -- 亲属距离等级
    c_kintype,  -- 亲属类型编码
    c_kintype_desc,  -- 亲属类型英文描述
    c_kintype_desc_chn,  -- 亲属类型中文描述
    c_notes,  -- 备注说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'KIN_MOURNING') }}
