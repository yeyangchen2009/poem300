{{ config(materialized='table') }}

-- ODS: 存储户籍状态分类代码表，包含户籍类型代码及其对应的中英文状态描述
-- 源表: HOUSEHOLD_STATUS_CODES（94557 行）

SELECT
    c_household_status_code,  -- 户籍状态分类代码，用于唯一标识不同的户籍类型（如民籍/军籍/匠籍等）
    c_household_status_desc,  -- 户籍状态英文描述（如'Civilian Household'）
    c_household_status_desc_chn,  -- 户籍状态中文描述（如'民籍'）
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'HOUSEHOLD_STATUS_CODES') }}
