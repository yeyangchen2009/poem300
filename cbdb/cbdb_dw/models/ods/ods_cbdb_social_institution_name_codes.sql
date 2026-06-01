{{ config(materialized='table') }}

-- ODS: 存储社会机构名称的标准编码及其对应的汉字与拼音表示，用于统一机构名称的标识和检索。
-- 源表: SOCIAL_INSTITUTION_NAME_CODES（136712 行）

SELECT
    c_inst_name_code,  -- 社会机构名称的唯一标识编码，用于关联其他表中机构名称信息
    c_inst_name_hz,  -- 社会机构名称的汉字表示，最大长度50字符
    c_inst_name_py,  -- 社会机构名称的拼音表示，用于拉丁化检索和标注
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_NAME_CODES') }}
