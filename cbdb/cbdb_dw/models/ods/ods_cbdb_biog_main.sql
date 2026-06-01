{{ config(materialized='table') }}

-- ODS: 存储人物核心传记信息的主表，包含人物的基本属性、生卒年份、籍贯信息、民族归属、行政编码及系统元数据等核心字段
-- 源表: BIOG_MAIN（28079 行）

SELECT
    c_personid,  -- 人物唯一标识符，系统主键
    c_name,  -- 人物姓名（拉丁化形式）
    c_name_chn,  -- 人物中文姓名
    c_index_year,  -- 索引年份（用于人物检索的时间基准）
    c_index_year_type_code,  -- 索引年份类型编码（关联INDEXYEAR_TYPE_CODES表）
    c_index_year_source_id,  -- 索引年份来源标识（关联文本来源表）
    c_female,  -- 性别标识（0=男性，1=女性）
    c_index_addr_id,  -- 标准籍贯地址ID（关联ADDRESSES表）
    c_index_addr_type_code,  -- 籍贯地址类型编码（关联BIOG_ADDR_CODES表）
    c_ethnicity_code,  -- 民族/族群编码（关联ETHNICITY_TRIBE_CODES表）
    c_household_status_code,  -- 户籍状态编码（关联HOUSEHOLD_STATUS_CODES表）
    c_tribe,  -- 部族/氏族名称（自由文本）
    c_birthyear,  -- 出生年份（公历年份）
    c_by_nh_code,  -- 出生年号编码（关联NIAN_HAO表）
    c_by_nh_year,  -- 出生年份在年号纪年中的具体年份
    c_by_range,  -- 出生年份范围编码（关联YEAR_RANGE_CODES表）
    c_deathyear,  -- 死亡年份（公历年份）
    c_dy_nh_code,  -- 死亡年号编码（关联NIAN_HAO表）
    c_dy_nh_year,  -- 死亡年份在年号纪年中的具体年份
    c_dy_range,  -- 死亡年份范围编码（关联YEAR_RANGE_CODES表）
    c_death_age,  -- 享寿年龄（整数）
    c_death_age_range,  -- 享寿年龄范围编码（关联YEAR_RANGE_CODES表）
    c_fl_earliest_year,  -- 人物活跃期最早年份
    c_fl_ey_nh_code,  -- 活跃期最早年份对应的年号编码
    c_fl_ey_nh_year,  -- 活跃期最早年份在年号纪年中的具体年份
    c_fl_ey_notes,  -- 活跃期最早年份备注
    c_fl_latest_year,  -- 人物活跃期最晚年份
    c_fl_ly_nh_code,  -- 活跃期最晚年份对应的年号编码
    c_fl_ly_nh_year,  -- 活跃期最晚年份在年号纪年中的具体年份
    c_fl_ly_notes,  -- 活跃期最晚年份备注
    c_surname,  -- 姓氏（拉丁化形式）
    c_surname_chn,  -- 姓氏（中文）
    c_mingzi,  -- 名字（拉丁化形式）
    c_mingzi_chn,  -- 名字（中文）
    c_dy,  -- 主要活动朝代编码（关联DYNASTIES表）
    c_choronym_code,  -- 郡望编码（关联CHORONYM_CODES表）
    c_notes,  -- 人物备注信息
    c_by_intercalary,  -- 出生日期是否包含闰月标记
    c_dy_intercalary,  -- 死亡日期是否包含闰月标记
    c_by_month,  -- 出生月份（农历）
    c_dy_month,  -- 死亡月份（农历）
    c_by_day,  -- 出生日期（农历日）
    c_dy_day,  -- 死亡日期（农历日）
    c_by_day_gz,  -- 出生日干支编码（关联GANZHI_CODES表）
    c_dy_day_gz,  -- 死亡日干支编码（关联GANZHI_CODES表）
    c_surname_proper,  -- 规范化的姓氏（拉丁化形式）
    c_mingzi_proper,  -- 规范化的名字（拉丁化形式）
    c_name_proper,  -- 规范化的全名（拉丁化形式）
    c_surname_rm,  -- 姓氏罗马化形式
    c_mingzi_rm,  -- 名字罗马化形式
    c_name_rm,  -- 全名罗马化形式
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'BIOG_MAIN') }}
