{{ config(materialized='table') }}

-- ODS: 存储不同状态代码及其描述的参考表，用于记录系统中使用的各种状态类型及其对应的中英文描述信息
-- 源表: STATUS_CODES（136746 行）

SELECT
    c_status_code,  -- 状态类型唯一标识代码，用于关联其他表中的状态信息
    c_status_desc,  -- 状态类型的英文描述文本，说明该状态代码代表的含义
    c_status_desc_chn,  -- 状态类型的中文描述文本，提供对应的中文释义说明
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'STATUS_CODES') }}
