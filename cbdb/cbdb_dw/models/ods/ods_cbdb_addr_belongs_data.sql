{{ config(materialized='table') }}

-- ODS: 存储地址归属关系的时序数据，记录特定地址在时间维度上所属的上级行政区划及其来源信息
-- 源表: ADDR_BELONGS_DATA（2 行）

SELECT
    c_addr_id,  -- 当前地址的唯一标识符，关联地址编码表(ADDR_CODES/ADDRESSES)的主键
    c_belongs_to,  -- 上级归属地址的唯一标识符，递归关联本表或地址编码表(ADDR_CODES/ADDRESSES)的c_addr_id
    c_firstyear,  -- 归属关系生效起始年份（公元纪年）
    c_lastyear,  -- 归属关系生效结束年份（公元纪年）
    c_source,  -- 资料来源标识符，关联文本资料表(TEXT_CODES)的c_textid字段
    c_pages,  -- 资料来源的具体页码或位置说明
    c_notes,  -- 关于该归属关系的补充说明或考证注释
    c_created_by,  -- 记录创建人
    c_created_date,  -- 记录创建时间
    c_modified_by,  -- 记录修改人
    c_modified_date,  -- 记录修改时间
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ADDR_BELONGS_DATA') }}
