{{ config(materialized='table') }}

-- ODS: 存储与亲属关系相关的丧服等级步骤信息，用于描述不同亲属关系在服丧期间的步骤计算规则
-- 源表: KIN_MOURNING_STEPS（107897 行）

SELECT
    c_kinrel,  -- 亲属关系代码，标识具体的亲属关系类型（如父子、兄弟等）
    c_upstep,  -- 向上步骤数，表示在家族谱系中向上追溯的代数
    c_dwnstep,  -- 向下步骤数，表示在家族谱系中向下追溯的代数
    c_marstep,  -- 婚姻步骤数，表示通过婚姻关系连接的步骤
    c_colstep,  -- 共同步骤数，表示共同祖先的代数或关联步骤
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'KIN_MOURNING_STEPS') }}
