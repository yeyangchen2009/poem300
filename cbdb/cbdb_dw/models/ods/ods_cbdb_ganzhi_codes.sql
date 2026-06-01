{{ config(materialized='table') }}

-- ODS: 存储干支代码及其对应的中文名称和拼音，用于表示中国传统历法中的干支纪年、纪日等信息。
-- 源表: GANZHI_CODES（94555 行）

SELECT
    c_ganzhi_code,  -- 干支的唯一标识代码，表示特定的干支组合（如甲子、乙丑等）。
    c_ganzhi_chn,  -- 干支的中文名称（汉字表示），例如'甲子'、'乙丑'等。
    c_ganzhi_py,  -- 干支的拼音（拉丁字母转写），例如'jiazi'、'yichou'等。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'GANZHI_CODES') }}
