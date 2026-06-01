{{ config(materialized='table') }}

-- ODS: 存储场合类型代码及其描述的编码表，用于标识不同社交或历史场合的类型，如文学创作场合、政治事件场合等。
-- 源表: OCCASION_CODES（107995 行）

SELECT
    c_occasion_code,  -- 场合类型的唯一标识代码，整数类型主键。
    c_occasion_desc,  -- 场合类型的英文描述，最大长度50字符。
    c_occasion_desc_chn,  -- 场合类型的中文描述，最大长度50字符。
    c_sortorder,  -- 排序序号，用于定义场合类型在列表中的显示顺序。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'OCCASION_CODES') }}
