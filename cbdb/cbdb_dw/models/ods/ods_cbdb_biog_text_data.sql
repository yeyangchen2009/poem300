{{ config(materialized='table') }}

-- ODS: 存储人物与文本关联信息，记录人物在特定文本中的角色及相关时间信息
-- 源表: BIOG_TEXT_DATA（86233 行）

SELECT
    c_textid,  -- 关联文本的唯一标识符，对应TEXT_CODES表的c_textid
    c_personid,  -- 人物唯一标识符，对应BIOG_MAIN表的c_personid
    c_role_id,  -- 角色类型代码，对应TEXT_ROLE_CODES表的c_role_id
    c_year,  -- 事件发生的年份（公历）
    c_nh_code,  -- 年号代码，对应NIAN_HAO表的c_nianhao_id
    c_nh_year,  -- 年号纪年对应的具体年份
    c_range_code,  -- 年份范围代码，对应YEAR_RANGE_CODES表的c_range_code
    c_source,  -- 数据来源标识符，可能关联TEXT_CODES表
    c_pages,  -- 原始文献中的页码或出处信息
    c_notes,  -- 附加说明或注释
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_TEXT_DATA') }}
