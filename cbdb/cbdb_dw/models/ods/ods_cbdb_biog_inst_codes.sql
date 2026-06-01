{{ config(materialized='table') }}

-- ODS: 存储人物与机构关联角色代码的字典表，定义不同机构角色类型及其描述信息
-- 源表: BIOG_INST_CODES（28058 行）

SELECT
    c_bi_role_code,  -- 机构角色代码，唯一标识人物在机构中担任的角色类型
    c_bi_role_desc,  -- 角色类型英文描述，说明机构角色的具体含义
    c_bi_role_chn,  -- 角色类型中文描述，说明机构角色的具体含义
    c_notes,  -- 附加注释，记录特殊说明或数据来源信息
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_INST_CODES') }}
