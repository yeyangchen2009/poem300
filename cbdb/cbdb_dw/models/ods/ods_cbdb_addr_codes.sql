{{ config(materialized='table') }}

-- ODS: 存储地址编码信息，包括地址的中英文名称、存在的时间范围、地理坐标及行政区类型等。
-- 源表: ADDR_CODES（589 行）

SELECT
    c_addr_id,  -- 地址的唯一标识符
    c_name,  -- 地址的英文名称
    c_name_chn,  -- 地址的中文名称
    c_firstyear,  -- 地址存在的起始年份
    c_lastyear,  -- 地址存在的结束年份
    c_admin_type,  -- 行政区类型（如省、州、县等）
    c_admin_cat_code,  -- 行政区类别编码
    x_coord,  -- 地理经度坐标
    y_coord,  -- 地理纬度坐标
    CHGIS_PT_ID,  -- 中国历史地理信息系统（CHGIS）中的点标识符
    c_notes,  -- 备注或附加信息
    c_alt_names,  -- 地址的备用名称或别名
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ADDR_CODES') }}
