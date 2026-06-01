{{ config(materialized='table') }}

-- ODS: 存储文本角色类型代码及其描述的代码表，用于标识文本创作、编辑或相关活动中涉及的不同角色类型
-- 源表: TEXT_ROLE_CODES（140596 行）

SELECT
    c_role_id,  -- 角色类型唯一标识符，主键字段
    c_role_desc,  -- 角色类型的英文描述（如作者、编者、注释者等）
    c_role_desc_chn,  -- 角色类型的中文描述（如：作者、编者、注释者等）
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_ROLE_CODES') }}
