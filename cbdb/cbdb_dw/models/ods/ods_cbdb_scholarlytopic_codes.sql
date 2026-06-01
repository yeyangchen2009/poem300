{{ config(materialized='table') }}

-- ODS: 存储学术主题分类代码及其描述信息，用于标识不同学术研究领域的中英文名称和分类信息
-- 源表: SCHOLARLYTOPIC_CODES（136465 行）

SELECT
    c_topic_code,  -- 学术主题的唯一标识代码
    c_topic_desc,  -- 学术主题的英文描述
    c_topic_desc_chn,  -- 学术主题的中文描述
    c_topic_type_code,  -- 学术主题类型分类代码
    c_topic_type_desc,  -- 学术主题类型的英文描述
    c_topic_type_desc_chn,  -- 学术主题类型的中文描述
    c_sortorder,  -- 排序序号，用于控制主题的显示顺序
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'SCHOLARLYTOPIC_CODES') }}
