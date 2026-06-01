{{ config(materialized='table') }}

-- ODS: 存储文献典籍的基本书目信息，包括标题、版本、出版信息、保存状态及相关参考链接等元数据
-- 源表: TEXT_CODES（138231 行）

SELECT
    c_textid,  -- 文献唯一标识符
    c_title_chn,  -- 文献中文标题
    c_title,  -- 文献标题（拼音/英文）
    c_title_trans,  -- 文献标题翻译
    c_text_type_id,  -- 文献类型标识，关联TEXT_TYPE表
    c_text_year,  -- 文献创作年份（公历年）
    c_text_nh_code,  -- 文献创作年号编码，关联NIAN_HAO表
    c_text_nh_year,  -- 文献创作年号年份
    c_text_range_code,  -- 文献创作时间范围编码，关联YEAR_RANGE_CODES表
    c_bibl_cat_code,  -- 书目分类编码，关联TEXT_BIBLCAT_CODES表
    c_extant,  -- 现存状态编码，关联EXTANT_CODES表
    c_text_country,  -- 文献创作国家编码，关联COUNTRY_CODES表
    c_text_dy,  -- 文献创作朝代编码，关联DYNASTIES表
    c_source,  -- 资料来源编码
    c_pages,  -- 资料来源页码
    c_url_api,  -- 文献API访问链接
    c_url_api_coda,  -- CODA平台API链接
    c_url_homepage,  -- 文献主页URL
    c_notes,  -- 附加注释
    c_title_alt_chn,  -- 文献中文别名
    c_created_by,  -- 创建者
    c_modified_by,  -- 最后修改者
    c_created_date,  -- 创建日期
    c_modified_date,  -- 最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_CODES') }}
