{{ config(materialized='table') }}

-- ODS: 官职代码表，存储不同官职的中文名称、拼音、翻译以及分类信息
-- 源表: OFFICE_CODES（107999 行）

SELECT
    c_office_id,  -- 官职的唯一标识符
    c_dy,  -- 关联的朝代代码，对应DYNASTIES表的c_dy字段
    c_office_pinyin,  -- 官职名称的拼音表示
    c_office_chn,  -- 官职的中文名称
    c_office_pinyin_alt,  -- 官职的备用拼音
    c_office_chn_alt,  -- 官职的备用中文名称
    c_office_trans,  -- 官职的英文翻译
    c_office_trans_alt,  -- 官职的备用英文翻译
    c_source,  -- 记录来源的文献ID，关联到来源表（如TEXT_CODES的c_textid）
    c_pages,  -- 来源文献中的页码
    c_notes,  -- 备注信息
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'OFFICE_CODES') }}
