{{ config(materialized='table') }}

-- ODS: 条目类型代码表，存储不同条目类型的代码及其描述。
-- 源表: ENTRY_CODES（87235 行）

SELECT
    c_entry_code,  -- 条目类型唯一标识代码，用于标识特定类型的条目（如科举考试类型、官职任命类型等）。
    c_entry_desc,  -- 条目类型的英文描述，简要说明该代码对应的条目类别或性质。
    c_entry_desc_chn,  -- 条目类型的中文描述，提供代码对应条目的中文名称或详细说明。
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ENTRY_CODES') }}
