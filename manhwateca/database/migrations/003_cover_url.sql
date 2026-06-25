ALTER TABLE manhwateca.mangas
ADD COLUMN IF NOT EXISTS cover_url TEXT;

DROP VIEW IF EXISTS manhwateca.vw_next_reads;
DROP VIEW IF EXISTS manhwateca.vw_mangas;

CREATE VIEW manhwateca.vw_mangas AS
SELECT
    m.id,
    m.work_code,
    m.title,
    m.alternative_title,
    m.interest_level,
    m.reading_status,
    m.reading_status_v2,
    m.personal_rank,
    m.score,
    m.last_read_chapter,
    m.latest_available_chapter,
    m.size_label,
    m.count_status,
    m.latest_mangaupdates_chapter,
    m.mangaupdates_url,
    m.spice_level,
    m.format,
    m.notion_page_id,
    m.notion_last_synced_at,
    m.notion_sync_status,
    m.created_at,
    m.updated_at,
    COALESCE(
        string_agg(t.name, ' | ' ORDER BY t.name)
            FILTER (WHERE t.name IS NOT NULL),
        ''
    ) AS themes,
    m.cover_url
FROM manhwateca.mangas m
LEFT JOIN manhwateca.manga_themes mt
    ON mt.manga_id = m.id
LEFT JOIN manhwateca.themes t
    ON t.id = mt.theme_id
GROUP BY m.id;

CREATE VIEW manhwateca.vw_next_reads AS
SELECT *
FROM manhwateca.vw_mangas
WHERE reading_status_v2 = 'Quero Ler'
ORDER BY
    CASE personal_rank
        WHEN 'Topzera' THEN 1
        WHEN 'Legalzin' THEN 2
        WHEN 'Normal' THEN 3
        WHEN 'Despriorizado' THEN 4
        ELSE 5
    END,
    title;
