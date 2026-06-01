{{ config(materialized='table') }}

-- ODS: 存储亲属关系类型代码及其相关属性，用于描述不同亲属关系的分类、中文称谓、代际步数和关系简化形式
-- 源表: KINSHIP_CODES（94561 行）

SELECT
    c_kincode,  -- 亲属关系类型唯一标识代码
    c_kin_pair1,  -- 亲属关系配对中第一个角色的关联代码
    c_kin_pair2,  -- 亲属关系配对中第二个角色的关联代码
    c_kin_pair_notes,  -- 亲属关系配对的说明注释
    c_kinrel_chn,  -- 亲属关系的中文称谓
    c_kinrel,  -- 亲属关系的英文/拼音描述
    c_kinrel_alt,  -- 亲属关系的替代描述
    c_pick_sorting,  -- 亲属关系在界面中的显示排序权重
    c_upstep,  -- 向上追溯的世代步数（如父亲为1步）
    c_dwnstep,  -- 向下追溯的世代步数（如儿子为1步）
    c_marstep,  -- 通过婚姻关系建立的亲属步数
    c_colstep,  -- 旁系亲属的世代步数（如堂兄弟为1步）
    c_kinrel_simplified,  -- 简化版的亲属关系描述（用于快速检索）
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'KINSHIP_CODES') }}
