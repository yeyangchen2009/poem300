{{ config(materialized='table') }}

-- ODS: 存储社会机构别名类型代码表，定义机构别名的分类编码标准
-- 源表: SOCIAL_INSTITUTION_ALTNAME_CODES（136590 行）

SELECT
    c_inst_altname_type,  -- 机构别名类型代码，唯一标识一种别名分类
    c_inst_altname_desc,  -- 机构别名类型英文描述，说明别名类型的性质或用途
    c_inst_altname_chn,  -- 机构别名类型中文描述，说明别名类型的汉字表示
    c_notes,  -- 备注字段，记录该别名类型代码的补充说明信息
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SOCIAL_INSTITUTION_ALTNAME_CODES') }}
