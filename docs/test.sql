-- =============================================================================
-- 诗人诗句「编年系地」SQL 集合
-- 数据库: cnkgraph/data/cnkgraph-merge.sqlite  (SQLite 3)
-- 表数  : 39 张；本文件聚焦其中 8 张核心表
-- 目标  : 回答「诗人在什么时间、什么地点、写了什么诗」
-- =============================================================================
--
-- 【核心 8 表关系】
--
--   person  ──< writing ──< writing_link >──┬── DateTime  (何时)
--        │                                  ├── Region   (何地，可多个)
--        │                                  ├── People   (写给谁 / 提到谁)
--        │                                  └── Scenery / Allusion ...
--        │
--        └─(biography_activity 理论存在但实际为空，故编年必须靠 writing_link 反推)
--
--   region          —— 当代行政区划（含经纬度）
--   region_history  —— 历史地名变迁（同名异位、古名→今名、含历史时期经纬度）
--   writing_clause  —— 诗句逐句
--
-- 【使用方法】
--   sqlite3 cnkgraph-merge.sqlite < docs/test.sql
--   或在 DBeaver / DB Browser for SQLite 中分段执行
--
-- 【关键坑】
--   writing_link.region_id 可能是逗号分隔的多值（"CN450802,CN341621112"），
--   不能直接 JOIN region；下方 §3 用递归 CTE 拆开。
-- =============================================================================


-- §1 ─────────────────────────── 单表速览 ─────────────────────────────────────
-- 目的：先把每张关键表"长什么样"看清楚，再写 JOIN。

-- 1.1 诗人
SELECT id, name, dynasty, birth_year, death_year FROM person;
--    15188 李白 盛唐 701 762
--    17270 杜甫 唐   712 770
--    18616 王维 盛唐 701 761

-- 1.2 诗作（仅看带时间/地点的）
SELECT id, author_id, author_name, title,
       author_date_raw,        -- 写作时间原始字符串（如"762年9月9日"）
       author_place_raw        -- 写作地点原始 region_id（如 CN340521）
FROM writing
WHERE author_date_raw IS NOT NULL AND author_date_raw != ''
LIMIT 10;

-- 1.3 写作链接（按 label_type 分类计数）
SELECT label_type, COUNT(*) AS n
FROM writing_link
GROUP BY label_type
ORDER BY n DESC;
--    Region     6288   ← 写作/提及地点
--    Allusion   4940   ← 用典
--    People     4215   ← 涉及人物
--    DateTime   3983   ← 写作时间
--    Scenery    3503
--    Title      1565
--    Plant       899
--    ...

-- 1.4 地点（当代）
SELECT id, name, latitude, longitude, parent_id
FROM region
WHERE latitude IS NOT NULL
LIMIT 8;

-- 1.5 历史地名（同名异位、古名今名映射）
SELECT region_id, name, new_name, type,
       begin_year, end_year, latitude, longitude
FROM region_history
WHERE latitude IS NOT NULL
LIMIT 8;

-- 1.6 诗句
SELECT id, writing_id, idx, content
FROM writing_clause
WHERE writing_id = 9050   -- 王维《九月九日忆山东兄弟》
ORDER BY idx;


-- §2 ─────────────────────── 单首诗的时间地点画像 ─────────────────────────────
-- 拿王维《九月九日忆山东兄弟》（writing_id = 9050）举例：
-- 「716 年 9 月 9 日」「地点 CN6101（陕西华州）」。

SELECT
    w.id           AS writing_id,
    w.author_name,
    w.title,
    w.author_date_raw,                        -- 诗作本身的原始时间
    w.author_place_raw,                       -- 诗作本身的原始地点 ID
    r.name        AS place_name,              -- 反查当代地名
    r.latitude,
    r.longitude,
    (SELECT GROUP_CONCAT(content, ' / ')
       FROM writing_clause c
      WHERE c.writing_id = w.id
      ORDER BY c.idx) AS full_text            -- 全文拼起来
FROM writing w
LEFT JOIN region r ON r.id = w.author_place_raw
WHERE w.id = 9050;


-- §3 ─────────────── 把 writing_link 的多值 region_id 拆开 ─────────────────────
-- 一首诗可能涉及多个地点（如"龙山"对应三个候选位置）。
-- SQLite 没有原生 SPLIT，用递归 CTE 把 "CN450802,CN341621112" 拆成两行。

WITH RECURSIVE
split_region(writing_id, label_identity, value, head, tail) AS (
    -- 起始：取出每个 Region 链接的完整 region_id 字符串
    SELECT writing_id, label_identity, value,
           -- head = 第一个逗号前的部分
           CASE WHEN INSTR(region_id, ',') > 0
                THEN SUBSTR(region_id, 1, INSTR(region_id, ',') - 1)
                ELSE region_id
           END,
           -- tail = 第一个逗号后的部分（用于下一轮递归）
           CASE WHEN INSTR(region_id, ',') > 0
                THEN SUBSTR(region_id, INSTR(region_id, ',') + 1)
                ELSE ''
           END
    FROM writing_link
    WHERE label_type = 'Region'
      AND region_id IS NOT NULL AND region_id != ''

    UNION ALL

    -- 递归：把 tail 继续拆
    SELECT writing_id, label_identity, value,
           CASE WHEN INSTR(tail, ',') > 0
                THEN SUBSTR(tail, 1, INSTR(tail, ',') - 1)
                ELSE tail
           END,
           CASE WHEN INSTR(tail, ',') > 0
                THEN SUBSTR(tail, INSTR(tail, ',') + 1)
                ELSE ''
           END
    FROM split_region
    WHERE tail != ''
)
SELECT writing_id, label_identity, value, head AS single_region_id
FROM split_region
LIMIT 10;
-- 输出每行一个 region_id，可以直接 JOIN region 表


-- §4 ─────────────── 诗作 × 时间 × 地点 × 经纬度（核心视图） ───────────────────
-- 「诗人在什么时间、什么地点、写了什么诗」的最简版。
-- 用 writing.author_date_raw + writing.author_place_raw（一首诗一行）。

SELECT
    w.author_name,
    w.title,
    w.author_date_raw                 AS write_date,        -- 时间（文本）
    dt.year                           AS write_year,        -- 从 link 抽取的年份（数值）
    r.id                              AS region_id,
    r.name                            AS place_name,        -- 地点（当代名）
    r.latitude,
    r.longitude
FROM writing w
-- 时间：从 writing_link 取最精确的年份（confidence=1 的优先）
LEFT JOIN writing_link dt
       ON dt.writing_id = w.id
      AND dt.label_type = 'DateTime'
      AND dt.year IS NOT NULL
      AND dt.confident_level = 1
-- 地点：直接用 writing 自带的 author_place_raw
LEFT JOIN region r ON r.id = w.author_place_raw
WHERE w.author_id = 15188                       -- 改成 17270=杜甫 / 18616=王维
  AND w.author_place_raw IS NOT NULL
  AND w.author_place_raw != ''
GROUP BY w.id                                    -- 一首诗去重
ORDER BY write_year, w.author_date_raw;


-- §5 ──────────── 一生轨迹：按年份排序的全部诗作 + 地点 ───────────────────────
-- 给定一个诗人，输出他的"编年诗地图"——这是地图联动的主要数据源。

WITH poet_writings AS (
    SELECT
        w.id            AS writing_id,
        w.title,
        w.author_date_raw,
        -- 取该诗最精确的年份（带月日的 confident=1 优先；其次任何 DateTime 的年份）
        COALESCE(
            (SELECT dt.year FROM writing_link dt
              WHERE dt.writing_id = w.id
                AND dt.label_type = 'DateTime'
                AND dt.year IS NOT NULL
                AND dt.confident_level = 1
              LIMIT 1),
            (SELECT dt.year FROM writing_link dt
              WHERE dt.writing_id = w.id
                AND dt.label_type = 'DateTime'
                AND dt.year IS NOT NULL
              LIMIT 1)
        ) AS year,
        w.author_place_raw AS primary_region_id
    FROM writing w
    WHERE w.author_id = 15188                     -- ← 改诗人 ID
)
SELECT
    pw.year,
    pw.author_date_raw           AS date_text,
    pw.title,
    r.name                       AS place_name,
    r.latitude,
    r.longitude,
    -- 该诗还提到了哪些其他地点（除了主地点外）
    (SELECT GROUP_CONCAT(DISTINCT r2.name, '、')
       FROM writing_link wl
       JOIN region r2 ON ',' || wl.region_id || ',' LIKE '%,' || r2.id || ',%'
      WHERE wl.writing_id = pw.writing_id
        AND wl.label_type = 'Region'
        AND r2.id != pw.primary_region_id) AS mentioned_places
FROM poet_writings pw
LEFT JOIN region r ON r.id = pw.primary_region_id
ORDER BY pw.year, pw.author_date_raw;


-- §6 ─────────────────────── 地点 × 诗作数 聚合 ───────────────────────────────
-- 「李白在哪些地方写了几首诗？」——地图热力图 / 气泡图的直接数据源。
-- 注：year 字段是 TEXT，含"去年""襄王"等非数字字符串，GLOB '[0-9]*' 过滤。

SELECT
    r.id              AS region_id,
    r.name            AS place_name,
    r.latitude,
    r.longitude,
    COUNT(DISTINCT w.id) AS poem_count,
    MIN(CAST(dt.year AS INTEGER)) AS first_year,
    MAX(CAST(dt.year AS INTEGER)) AS last_year,
    -- 这一地点的代表诗作（取 3 首）
    (SELECT GROUP_CONCAT(title, '、')
       FROM (
         SELECT w2.title FROM writing w2
         JOIN writing_link wl2 ON wl2.writing_id = w2.id
          AND wl2.label_type = 'Region'
          AND ',' || wl2.region_id || ',' LIKE '%,' || r.id || ',%'
         WHERE w2.author_id = 15188
         ORDER BY dt.year LIMIT 3
       )
    ) AS sample_titles
FROM writing w
JOIN writing_link wl
     ON wl.writing_id = w.id
    AND wl.label_type = 'Region'
    AND wl.region_id IS NOT NULL AND wl.region_id != ''
JOIN region r
     ON ',' || wl.region_id || ',' LIKE '%,' || r.id || ',%'
LEFT JOIN writing_link dt
     ON dt.writing_id = w.id
    AND dt.label_type = 'DateTime'
    AND dt.year IS NOT NULL
    AND dt.year GLOB '[0-9]*'                    -- 过滤掉"去年""襄王"等非数字
WHERE w.author_id = 15188                          -- ← 改诗人 ID
GROUP BY r.id
ORDER BY poem_count DESC;


-- §7 ───────────── 历史地名处理（唐代"南京" ≠ 现代南京）──────────────────────
-- 唐代「南京」= 今成都；现代「南京」= 江苏南京。
-- 用 region_history 把诗作时间映射到「该时期叫什么名字 + 当时经纬度」。

SELECT
    w.title,
    w.author_date_raw,
    dt.year                        AS write_year,
    rh.name                        AS historical_name,    -- 该地名在写作年份时的古称
    rh.new_name                    AS modern_equivalent,
    rh.latitude,
    rh.longitude,
    rh.begin_year,
    rh.end_year
FROM writing w
JOIN writing_link wl
     ON wl.writing_id = w.id
    AND wl.label_type = 'Region'
JOIN writing_link dt
     ON dt.writing_id = w.id
    AND dt.label_type = 'DateTime'
    AND dt.year IS NOT NULL
JOIN region_history rh
     ON rh.region_id = wl.region_id
    AND dt.year BETWEEN rh.begin_year AND rh.end_year
WHERE w.author_id = 15188
LIMIT 10;


-- §8 ─────────────────── 一首诗里提到的全部"地理实体" ────────────────────────
-- Region + Scenery 都算地理实体（一首都城、一座山）。
-- 适合在地图上点出"诗中提到的地方"。

SELECT
    wl.writing_id,
    w.title,
    wl.label_type,                              -- Region / Scenery
    wl.value,                                   -- 文本（如"龙山"）
    wl.region_id,                               -- 关联的 region_id（可能多个）
    r.latitude,
    r.longitude
FROM writing_link wl
JOIN writing w ON w.id = wl.writing_id
LEFT JOIN region r ON r.id =
    -- region_id 可能是逗号分隔的，取第一个作为代表点
    CASE WHEN INSTR(wl.region_id, ',') > 0
         THEN SUBSTR(wl.region_id, 1, INSTR(wl.region_id, ',') - 1)
         ELSE wl.region_id
    END
WHERE wl.writing_id = 25516                     -- 《九日龙山饮》
  AND wl.label_type IN ('Region', 'Scenery')
ORDER BY wl.label_type;


-- §9 ─────────────────── 诗人年表（弥补 biography_activity 空表）──────────────
-- 由于 biography_activity 当前没有数据，我们用「按年份分组、该年所有诗作 +
-- 该年诗人活跃地点」拼出一张伪年表。

SELECT
    dt.year                              AS year,
    COUNT(DISTINCT w.id)                 AS poem_count,
    GROUP_CONCAT(DISTINCT w.title, '、') AS titles,
    -- 该年去过的地方（去重）
    (SELECT GROUP_CONCAT(DISTINCT r.name, '、')
       FROM writing w2
       JOIN writing_link wl2 ON wl2.writing_id = w2.id
        AND wl2.label_type = 'Region'
       JOIN region r ON ',' || wl2.region_id || ',' LIKE '%,' || r.id || ',%'
      WHERE w2.author_id = 15188
        AND EXISTS (
            SELECT 1 FROM writing_link dt2
             WHERE dt2.writing_id = w2.id
               AND dt2.label_type = 'DateTime'
               AND dt2.year = dt.year
        )
    ) AS places_visited
FROM writing w
JOIN writing_link dt
     ON dt.writing_id = w.id
    AND dt.label_type = 'DateTime'
    AND dt.year IS NOT NULL
WHERE w.author_id = 15188                          -- ← 改诗人 ID
GROUP BY dt.year
ORDER BY dt.year;


-- §10 ──────────────────── GeoJSON 风格输出（地图直用）───────────────────────
-- 直接把上面 §5 的结果格式化成 GeoJSON FeatureCollection，前端 map 可直接 load。
-- 注：SQLite 字符串拼接用 ||；下面的 SQL 会产出**一行一 Feature** 的拼接。
-- 更稳妥的做法是 Python 取数后用 json.dumps 组装；这里仅演示 SQL 可达。

WITH features AS (
    SELECT
        '{"type":"Feature","geometry":{"type":"Point","coordinates":['
        || r.longitude || ',' || r.latitude
        || ']},'
        || '"properties":{'
        || '"title":"' || REPLACE(w.title, '"', '\"') || '",'
        || '"author":"' || w.author_name || '",'
        || '"year":' || COALESCE(dt.year, 'null') || ','
        || '"date":"' || COALESCE(w.author_date_raw, '') || '",'
        || '"place":"' || COALESCE(r.name, '') || '"'
        || '}}' AS feature
    FROM writing w
    LEFT JOIN writing_link dt
           ON dt.writing_id = w.id
          AND dt.label_type = 'DateTime'
          AND dt.year IS NOT NULL
          AND dt.confident_level = 1
    LEFT JOIN region r ON r.id = w.author_place_raw
    WHERE w.author_id = 15188
      AND r.latitude IS NOT NULL
    GROUP BY w.id
    ORDER BY dt.year
)
SELECT
    '{"type":"FeatureCollection","features":['
    || GROUP_CONCAT(feature, ',')
    || ']}' AS geojson
FROM features;
-- 把这一行结果保存为 libai.geojson，前端 Leaflet/Mapbox 直接 L.geoJSON(data) 即可。


-- §11 ──────────────────────── 关键索引建议 ──────────────────────────────────
-- 当前 schema 已建：idx_writing_link_writing / idx_writing_link_type /
-- idx_writing_link_region。对编年系地再补一条复合索引会更稳：

-- CREATE INDEX IF NOT EXISTS idx_writing_link_dt_year
--     ON writing_link(label_type, year, confident_level);
-- CREATE INDEX IF NOT EXISTS idx_region_history_region_year
--     ON region_history(region_id, begin_year, end_year);

-- =============================================================================
-- 思维导图（对应 11 节）
--
--   诗人(§1.1) ─── 时间(§1.3 DateTime) ─── 地点(§1.3 Region, §1.4, §1.5)
--        │              │                       │
--        │              │                       │
--        └──────► 写作(§1.2, §2 单首画像)
--                          │
--                          ├── 拆多值(§3) ──► 诗作×地点视图(§4, §5 一生轨迹)
--                          │                       │
--                          │                       ├── 聚合热力(§6)
--                          │                       ├── 历史地名(§7)
--                          │                       └── 地理实体(§8)
--                          │
--                          └── 年表(§9) ──► GeoJSON(§10) ──► 地图(见 prd-map.md)
-- =============================================================================
