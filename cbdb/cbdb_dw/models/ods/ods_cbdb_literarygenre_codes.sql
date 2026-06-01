{{ config(materialized='table') }}

-- ODS: 存储文学体裁的代码及其描述。包含中文和英文的体裁名称，以及用于排序的字段。
-- 源表: LITERARYGENRE_CODES（107899 行）

SELECT
    c_lit_genre_code,  -- 文学体裁的唯一标识代码
    c_lit_genre_desc,  -- 文学体裁的英文描述
    c_lit_genre_desc_chn,  -- 文学体裁的中文描述
    c_sortorder,  -- 用于控制显示或查询时的排序顺序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'LITERARYGENRE_CODES') }}
