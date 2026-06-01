{{ config(materialized='table') }}

-- ODS: 存储个人财产及相关活动记录信息，包括财产获取、转让等行为的时间、数量、计量单位和地理位置信息
-- 源表: POSSESSION_DATA（109277 行）

SELECT
    c_personid,  -- 关联人物ID，对应 BIOG_MAIN 表的 c_personid
    c_possession_record_id,  -- 财产记录唯一标识符
    c_sequence,  -- 同一记录中多个事件的顺序编号
    c_possession_act_code,  -- 财产行为类型代码，关联 POSSESSION_ACT_CODES 表
    c_possession_desc,  -- 财产行为描述（英文）
    c_possession_desc_chn,  -- 财产行为描述（中文）
    c_quantity,  -- 财产数量
    c_measure_code,  -- 计量单位代码，关联 MEASURE_CODES 表
    c_possession_yr,  -- 财产行为发生的年份（公历年）
    c_possession_nh_code,  -- 财产行为发生的年号代码，关联 NIAN_HAO 表
    c_possession_nh_yr,  -- 年号纪年中的具体年份
    c_possession_yr_range,  -- 年份范围代码，关联 YEAR_RANGE_CODES 表
    c_addr_id,  -- 财产相关地理位置ID，关联 ADDR_CODES 表
    c_source,  -- 资料来源ID，关联 TEXT_CODES 表
    c_pages,  -- 资料引用页码或位置
    c_notes,  -- 附加注释
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'POSSESSION_DATA') }}
