{{ config(materialized='table') }}

-- ODS: 存储不同索引年份类型的代码表，用于定义人物传记中使用的年份类型标准
-- 源表: INDEXYEAR_TYPE_CODES（94559 行）

SELECT
    c_index_year_type_code,  -- 索引年份类型代码，唯一标识符，用于关联其他表中使用的年份类型
    c_index_year_type_desc,  -- 索引年份类型的英文描述，说明该代码对应的年份类型含义
    c_index_year_type_hz,  -- 索引年份类型的中文汉字描述，提供中文语境下的类型说明
    c_notes,  -- 附加注释字段，记录该年份类型代码的特殊说明或使用限制
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'INDEXYEAR_TYPE_CODES') }}
