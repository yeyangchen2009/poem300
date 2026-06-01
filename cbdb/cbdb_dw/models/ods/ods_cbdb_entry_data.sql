{{ config(materialized='table') }}

-- ODS: 记录人物的入仕途径及相关信息，包括科举、荫补、举荐等入仕方式的详细数据
-- 源表: ENTRY_DATA（87244 行）

SELECT
    c_personid,  -- 关联到 BIOG_MAIN 表的人物唯一标识符
    c_entry_code,  -- 关联到 ENTRY_CODES 表的入仕途径类型代码
    c_sequence,  -- 同一人物多条入仕记录的排序序号
    c_exam_rank,  -- 科举考试中的排名（如进士甲科、乙科等）
    c_kin_code,  -- 关联亲属关系的代码（如荫补入仕的亲属类型）
    c_kin_id,  -- 关联亲属的具体人物ID（若通过亲属关系入仕）
    c_assoc_code,  -- 关联社会关系的类型代码（如举荐人类型）
    c_assoc_id,  -- 关联社会关系的具体人物ID（如举荐人ID）
    c_year,  -- 入仕年份（绝对年份，若已知）
    c_age,  -- 入仕时的年龄（若记录）
    c_entry_nh_id,  -- 入仕年号ID
    c_entry_nh_year,  -- 年号纪年中的具体年份（如“贞观三年”中的3）
    c_entry_dy,  -- 入仕朝代编码
    c_entry_range,  -- 关联到 YEAR_RANGE_CODES 表的年份范围代码（若年份不精确）
    c_inst_code,  -- 关联到 SOCIAL_INSTITUTION_CODES 表的社会机构代码（如科举考场机构）
    c_inst_name_code,  -- 关联到 SOCIAL_INSTITUTION_NAME_CODES 表的具体机构名称代码
    c_exam_field,  -- 科举考试科目或领域（如明经科、进士科）
    c_entry_addr_id,  -- 关联到 ADDRESSES 表的入仕地点ID（如科举考试地点）
    c_parental_status_code,  -- 父辈身份状态编码
    c_attempt_count,  -- 入仕尝试次数（如科举落第次数）
    c_source,  -- 关联到 TEXT_CODES 表的资料来源文本ID
    c_pages,  -- 资料来源的具体页码或章节
    c_notes,  -- 入仕记录的补充注释
    c_posting_notes,  -- 与入仕后官职任命相关的备注
    c_created_by,  -- 记录创建者标识
    c_modified_by,  -- 记录最后修改者标识
    c_created_date,  -- 记录创建日期
    c_modified_date,  -- 记录最后修改日期
    CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间
    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期
FROM {{ source('cbdb_src', 'ENTRY_DATA') }}
