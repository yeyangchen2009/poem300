{{ config(materialized='table') }}

-- ODS: 存储中国历史人物郡望代码的标准化编码表，用于记录不同姓氏家族的地理渊源信息
-- 源表: CHORONYM_CODES（87227 行）

SELECT
    c_choronym_code,  -- 郡望唯一标识代码，数字类型主键
    c_choronym_desc,  -- 郡望的英文文字描述，记录郡望的地理或历史特征
    c_choronym_chn,  -- 郡望的中文汉字表达，包含标准汉字名称
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'CHORONYM_CODES') }}
