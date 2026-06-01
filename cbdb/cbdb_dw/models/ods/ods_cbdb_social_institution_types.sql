{{ config(materialized='table') }}

-- ODS: 存储社会机构类型的编码表，包含机构类型的拼音缩写和汉字表示
-- 源表: SOCIAL_INSTITUTION_TYPES（136744 行）

SELECT
    c_inst_type_code,  -- 社会机构类型的唯一编码标识符
    c_inst_type_py,  -- 社会机构类型的拼音（罗马化）名称
    c_inst_type_hz,  -- 社会机构类型的中文汉字名称
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_TYPES') }}
