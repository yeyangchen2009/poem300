{{ config(materialized='table') }}

-- ODS: 存储人物社会关系数据的核心表，记录人物之间的亲属关系、社交关联及关联事件的具体信息
-- 源表: ASSOC_DATA（6301 行）

SELECT
    c_assoc_code,  -- 关联类型代码，关联ASSOC_CODES表定义关系类型
    c_personid,  -- 主人物ID，关联BIOG_MAIN表
    c_kin_code,  -- 亲属关系代码，关联KINSHIP_CODES表
    c_kin_id,  -- 亲属关系实例ID，用于区分同一类型的不同亲属关系
    c_assoc_id,  -- 关联实例唯一标识符
    c_assoc_kin_code,  -- 关联对象的亲属关系代码，关联KINSHIP_CODES表
    c_assoc_kin_id,  -- 关联对象的亲属关系实例ID
    c_tertiary_personid,  -- 第三方参与人物ID，关联BIOG_MAIN表
    c_tertiary_type_notes,  -- 第三方参与类型的文字说明
    c_assoc_count,  -- 关联事件发生次数
    c_sequence,  -- 同一关联事件的顺序编号
    c_assoc_first_year,  -- 社交关系起始年份
    c_assoc_last_year,  -- 社交关系结束年份
    c_source,  -- 资料来源代码，关联TEXT_CODES表
    c_pages,  -- 资料来源页码或卷册信息
    c_notes,  -- 关联事件备注说明
    c_assoc_fy_nh_code,  -- 起始年年号编码
    c_assoc_fy_nh_year,  -- 起始年年号年份
    c_assoc_fy_range,  -- 起始年年份范围标识
    c_assoc_ly_nh_code,  -- 结束年年号编码
    c_assoc_ly_nh_year,  -- 结束年年号年份
    c_assoc_ly_range,  -- 结束年年份范围标识
    c_addr_id,  -- 关联发生地点ID，关联ADDRESSES表
    c_litgenre_code,  -- 文学体裁代码，关联LITERARYGENRE_CODES表
    c_occasion_code,  -- 社交场合代码，关联OCCASION_CODES表
    c_topic_code,  -- 学术主题代码，关联SCHOLARLYTOPIC_CODES表
    c_inst_code,  -- 机构类型代码，关联SOCIAL_INSTITUTION_TYPES表
    c_inst_name_code,  -- 机构名称代码，关联SOCIAL_INSTITUTION_NAME_CODES表
    c_text_title,  -- 关联文献标题（强制存储原始汉字）
    c_assoc_claimer_id,  -- 关联主张者ID，关联BIOG_MAIN表
    c_assoc_fy_intercalary,  -- 起始年闰月标识
    c_assoc_fy_month,  -- 起始年月份
    c_assoc_fy_day,  -- 起始年日期
    c_assoc_fy_day_gz,  -- 起始年日干支编码
    c_assoc_ly_intercalary,  -- 结束年闰月标识
    c_assoc_ly_month,  -- 结束年月份
    c_assoc_ly_day,  -- 结束年日期
    c_assoc_ly_day_gz,  -- 结束年日干支编码
    c_created_by,  -- 记录创建者
    c_modified_by,  -- 最后修改者
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ASSOC_DATA') }}
