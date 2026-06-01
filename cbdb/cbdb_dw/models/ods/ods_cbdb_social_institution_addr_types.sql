{{ config(materialized='table') }}

-- ODS: 存储社会机构地址类型编码表，定义社会机构不同地址类型的分类标准与描述信息
-- 源表: SOCIAL_INSTITUTION_ADDR_TYPES（136588 行）

SELECT
    c_inst_addr_type_code,  -- 社会机构地址类型唯一编码标识符，数字型主键
    c_inst_addr_type_desc,  -- 地址类型的英文描述文本，说明地址类型的性质和用途
    c_inst_addr_type_chn,  -- 地址类型的中文描述文本，说明地址类型的性质和用途
    c_notes,  -- 地址类型相关补充说明或注释信息
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_ADDR_TYPES') }}
