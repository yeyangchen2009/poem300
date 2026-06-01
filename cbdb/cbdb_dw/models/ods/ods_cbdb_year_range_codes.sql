{{ config(materialized='table') }}

-- ODS: 存储年份范围代码及其对应的中英文描述，用于标识时间范围的精度和近似值。
-- 源表: YEAR_RANGE_CODES（140603 行）

SELECT
    c_range_code,  -- 年份范围唯一标识代码，用于关联其他表中时间范围字段
    c_range,  -- 年份范围的英文描述（如：Exact year, Circa等）
    c_range_chn,  -- 年份范围的中文描述（如：确年、大约等）
    c_approx,  -- 约数标识英文
    c_approx_chn,  -- 约数标识中文
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'YEAR_RANGE_CODES') }}
