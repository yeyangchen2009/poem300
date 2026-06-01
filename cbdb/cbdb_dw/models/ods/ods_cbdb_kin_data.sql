{{ config(materialized='table') }}

-- ODS: 存储人物的亲属关系数据，包括亲属的ID、亲属关系代码、来源及注释等信息
-- 源表: KIN_DATA（94574 行）

SELECT
    c_personid,  -- 主人物ID，关联BIOG_MAIN表的c_personid字段
    c_kin_id,  -- 亲属人物ID，关联BIOG_MAIN表的c_personid字段
    c_kin_code,  -- 亲属关系代码，关联KINSHIP_CODES表的c_kincode字段
    c_source,  -- 数据来源的文本ID（可能关联其他来源表）
    c_pages,  -- 来源文献的页码或位置信息
    c_notes,  -- 关于该亲属关系的补充注释
    c_autogen_notes,  -- 系统自动生成的备注信息
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'KIN_DATA') }}
