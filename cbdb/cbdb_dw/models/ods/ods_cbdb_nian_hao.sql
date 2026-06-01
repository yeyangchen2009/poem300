{{ config(materialized='table') }}

-- ODS: 存储中国历史年号信息表，记录年号的官方中文名称、拼音转写、使用朝代和使用时间范围
-- 源表: NIAN_HAO（107983 行）

SELECT
    c_nianhao_id,  -- 年号唯一标识符，主键ID
    c_dy,  -- 关联朝代表的朝代编号，对应DYNASTIES表的c_dy字段
    c_dynasty_chn,  -- 朝代中文名称（如：唐、宋、元等）
    c_nianhao_chn,  -- 年号正式中文名称（如：贞观、开元、洪武）
    c_nianhao_pin,  -- 年号拼音转写（如：zhengguan、kaiyuan、hongwu）
    c_firstyear,  -- 年号开始使用的公历年份
    c_lastyear,  -- 年号结束使用的公历年份
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'NIAN_HAO') }}
