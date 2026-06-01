{{ config(materialized='table') }}

-- ODS: 存储文本实例数据，记录文献不同版本或实例的出版信息、存世状态及相关元数据
-- 源表: TEXT_INSTANCE_DATA（140262 行）

SELECT
    c_textid,  -- 关联主文本的唯一标识符，外键参考TEXT_CODES.c_textid
    c_text_edition_id,  -- 文本版本的唯一标识符
    c_text_instance_id,  -- 文本实例的唯一标识符
    c_instance_title_chn,  -- 文本实例的中文标题
    c_instance_title,  -- 文本实例的拼音/英文标题
    c_instance_title_trans,  -- 文本实例的翻译标题
    c_part_of_instance,  -- 所属父实例的标识符
    c_part_of_instance_notes,  -- 所属父实例关系的注释
    c_pub_country,  -- 出版国家代码，外键参考COUNTRY_CODES.c_country_code
    c_pub_dy,  -- 出版朝代代码，外键参考DYNASTIES.c_dy
    c_pub_year,  -- 出版年份（文字描述）
    c_pub_nh_code,  -- 出版年号代码，外键参考NIAN_HAO.c_nianhao_id
    c_pub_nh_year,  -- 年号对应的具体年份
    c_pub_range_code,  -- 出版时间范围代码，外键参考YEAR_RANGE_CODES.c_range_code
    c_pub_loc,  -- 出版地点描述
    c_publisher,  -- 出版商/机构名称
    c_print,  -- 印刷版本信息
    c_pub_notes,  -- 出版相关补充说明
    c_source,  -- 资料来源代码，外键参考TEXT_CODES.c_textid
    c_pages,  -- 资料引用页码
    c_extant,  -- 存世状态代码，外键参考EXTANT_CODES.c_extant_code
    c_url_api,  -- 相关API访问链接
    c_url_homepage,  -- 相关主页链接
    c_notes,  -- 自由文本注释
    c_number,  -- 编号/流水号
    c_counter,  -- 计数器/统计标识
    c_title_alt_chn,  -- 替代中文标题
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 记录最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'TEXT_INSTANCE_DATA') }}
