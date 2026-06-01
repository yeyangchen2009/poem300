{{ config(materialized='table') }}

-- ODS: 存储财产行为类型编码表，用于标准化描述个人财产相关操作行为(如继承/捐赠/购置等)的编码对照信息
-- 源表: POSSESSION_ACT_CODES（109273 行）

SELECT
    c_possession_act_code,  -- 财产行为类型唯一标识编码
    c_possession_act_desc,  -- 财产行为类型的英文描述
    c_possession_act_desc_chn,  -- 财产行为类型的中文描述
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSSESSION_ACT_CODES') }}
