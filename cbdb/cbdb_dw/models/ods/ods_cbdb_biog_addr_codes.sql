{{ config(materialized='table') }}

-- ODS: 存储人物地址类型代码及其描述信息，用于定义不同地址类型的分类标准和索引排序规则
-- 源表: BIOG_ADDR_CODES（15209 行）

SELECT
    c_addr_type,  -- 地址类型唯一编码（主标识符）
    c_addr_desc,  -- 地址类型英文描述（如籍贯/居住地/墓葬地等）
    c_addr_desc_chn,  -- 地址类型中文描述（如：籍贯/居住地/墓葬地等）
    c_addr_note,  -- 地址类型补充说明
    c_index_addr_rank,  -- 地址类型在索引中的排序权重值
    c_index_addr_default_rank,  -- 地址类型默认索引排序等级
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_ADDR_CODES') }}
