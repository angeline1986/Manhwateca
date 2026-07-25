import json
from dataclasses import dataclass
from datetime import datetime

from manhwateca.database.connection import connect
from manhwateca.database.models import MangaRecord, manga_from_row
from manhwateca.notion_sync import statuses
from manhwateca.notion_sync.matching import normalize_title


@dataclass(frozen=True)
class MangaUpdatesConfirmationResult:
    status: str
    work_id: int | None = None
    series_id: str | None = None
    existing_work_id: int | None = None
    existing_title: str | None = None
    message: str | None = None

    @property
    def applied(self) -> bool:
        return self.status in {"applied", "already_applied"}

    def __bool__(self) -> bool:
        return self.applied


@dataclass(frozen=True)
class ConfirmedIdCorrectionResult:
    status: str
    work_id: int | None = None
    old_series_id: str | None = None
    new_series_id: str | None = None
    existing_work_id: int | None = None
    existing_title: str | None = None
    invalidated_fields: tuple[str, ...] = ()
    notion_sync_status: str | None = None
    expected_current_work_code: str | None = None
    actual_current_work_code: str | None = None
    message: str | None = None

    @property
    def applied(self) -> bool:
        return self.status == "applied"

    def __bool__(self) -> bool:
        return self.applied


class MangaRepository:
    def __init__(self, connection=None, *, connection_factory=None):
        self.connection = connection
        self.connection_factory = connection_factory or connect

    def list_mangas(self) -> list[MangaRecord]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM vw_mangas
            ORDER BY title
            """
        )
        return [manga_from_row(row) for row in rows]

    def list_mangas_by_ids(self, work_ids) -> list[MangaRecord]:
        ids = _normalize_ids(work_ids)
        if not ids:
            return []
        rows = self._fetch_all(
            """
            SELECT *
            FROM vw_mangas
            WHERE id = ANY(%s)
            ORDER BY title
            """,
            (ids,),
        )
        return [manga_from_row(row) for row in rows]

    def list_next_reads(self) -> list[MangaRecord]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM vw_next_reads
            """
        )
        return [manga_from_row(row) for row in rows]

    def find_by_work_code(self, work_code) -> MangaRecord | None:
        if work_code is None or str(work_code).strip() == "":
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM vw_mangas
            WHERE work_code = %s
            LIMIT 1
            """,
            (str(work_code).strip(),),
        )
        return manga_from_row(row) if row else None

    def find_by_id(self, work_id) -> MangaRecord | None:
        try:
            normalized_id = int(work_id)
        except (TypeError, ValueError):
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM vw_mangas
            WHERE id = %s
            LIMIT 1
            """,
            (normalized_id,),
        )
        return manga_from_row(row) if row else None

    def _find_by_id_for_update(self, work_id) -> MangaRecord | None:
        try:
            normalized_id = int(work_id)
        except (TypeError, ValueError):
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM mangas
            WHERE id = %s
            FOR UPDATE
            """,
            (normalized_id,),
        )
        return manga_from_row(row) if row else None

    def find_by_notion_page_id(self, page_id: str) -> MangaRecord | None:
        if not page_id:
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM vw_mangas
            WHERE notion_page_id = %s
            LIMIT 1
            """,
            (page_id,),
        )
        return manga_from_row(row) if row else None

    def find_by_normalized_title(self, title: str) -> MangaRecord | None:
        normalized = normalize_title(title)
        if not normalized:
            return None

        for manga in self.list_mangas():
            names = [manga.title, manga.alternative_title or ""]
            if normalized in {
                normalize_title(name)
                for value in names
                for name in str(value).split("|")
                if name.strip()
            }:
                return manga
        return None

    def save_catalog_mangas(self, mangas) -> int:
        saved = 0
        for manga in mangas:
            self.save_catalog_manga(manga)
            saved += 1
        self._connection().commit()
        return saved

    def save_catalog_manga(self, manga: dict) -> int:
        existing = self._find_catalog_match(manga)
        if existing:
            self._update_catalog_manga(existing.id, manga)
            self._connection().commit()
            return existing.id
        manga_id = self._insert_catalog_manga(manga)
        self._connection().commit()
        return manga_id

    def get_or_create_theme(self, name: str) -> int:
        name = str(name or "").strip()
        if not name:
            raise ValueError("Nome da temática é obrigatório.")

        existing = self._fetch_one(
            """
            SELECT id
            FROM themes
            WHERE lower(name) = lower(%s)
            LIMIT 1
            """,
            (name,),
        )
        if existing:
            return existing["id"]

        row = self._fetch_one(
            """
            INSERT INTO themes (name)
            VALUES (%s)
            RETURNING id
            """,
            (name,),
        )
        return row["id"]

    def add_theme_to_manga(self, manga_id: int, theme_name: str) -> int:
        theme_id = self.get_or_create_theme(theme_name)
        self._execute(
            """
            INSERT INTO manga_themes (manga_id, theme_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (manga_id, theme_id),
        )
        return theme_id

    def replace_manga_themes(self, manga_id: int, theme_names) -> list[int]:
        self._execute(
            """
            DELETE FROM manga_themes
            WHERE manga_id = %s
            """,
            (manga_id,),
        )
        theme_ids = []
        for name in theme_names:
            if str(name or "").strip():
                theme_ids.append(self.add_theme_to_manga(manga_id, name))
        return theme_ids

    def update_editorial_fields(self, name: str, changes: dict) -> bool:
        manga = self.find_by_normalized_title(name)
        if manga is None:
            return False

        values = _editorial_values(changes)
        if values:
            assignments = ", ".join(f"{column} = %s" for column in values)
            self._execute(
                f"""
                UPDATE mangas
                SET {assignments}
                WHERE id = %s
                """,
                (*values.values(), manga.id),
            )

        themes = _theme_values(changes)
        if themes is not None:
            self.replace_manga_themes(manga.id, themes)

        self._connection().commit()
        return True

    def append_alternative_title(self, manga_id: int, alias: str) -> dict | None:
        alias = str(alias or "").strip()
        if not alias:
            return None

        row = self._fetch_one(
            """
            SELECT alternative_title
            FROM mangas
            WHERE id = %s
            LIMIT 1
            """,
            (manga_id,),
        )
        if row is None:
            return None

        previous = row.get("alternative_title") or ""
        aliases = [
            item.strip()
            for item in previous.split("|")
            if item.strip()
        ]
        normalized_aliases = {normalize_title(item) for item in aliases}
        if normalize_title(alias) in normalized_aliases:
            return {
                "changed": False,
                "previous": previous,
                "current": previous,
            }

        aliases.append(alias)
        current = " | ".join(aliases)
        self._execute(
            """
            UPDATE mangas
            SET alternative_title = %s
            WHERE id = %s
            """,
            (current, manga_id),
        )
        self._connection().commit()
        return {
            "changed": True,
            "previous": previous,
            "current": current,
        }



    def update_mangaupdates_fields(
        self,
        name: str,
        series_id,
        summary: dict,
    ) -> bool:
        # Tenta localizar a obra
        manga = self.find_by_work_code(series_id)
        if manga is None:
            manga = self.find_by_normalized_title(name)
        
        if manga is None:
            return False

        # Mapeamento seguro: tenta buscar o dado em qualquer chave que a API possa ter retornado
        mu_url = summary.get("url") or summary.get("mangaupdates_url") or summary.get("mangaupdatesUrl")
        mu_cover = summary.get("cover_url") or summary.get("cover") or summary.get("coverUrl")
        mu_chapter = summary.get("latest_chapter") or summary.get("latest_mangaupdates_chapter")
        mu_format = summary.get("format") or summary.get("type")
        mu_alias = select_alternative_title(
            summary.get("associated_titles"),
            manga.title,
            series_id,
        )

        # SQL Direto: atualiza os campos com o que veio da API
        self._execute(
            """
            UPDATE mangas
            SET
                work_code = %s,
                latest_mangaupdates_chapter = %s,
                mangaupdates_url = %s,
                cover_url = %s,
                format = %s,
                alternative_title = CASE
                    WHEN alternative_title IS NULL OR BTRIM(alternative_title) = ''
                    THEN %s
                    ELSE alternative_title
                END
            WHERE id = %s
            """,
            (
                _string_or_none(series_id),
                _empty_to_none(mu_chapter),
                _empty_to_none(mu_url),
                _empty_to_none(mu_cover),
                _empty_to_none(mu_format),
                mu_alias,
                manga.id,
            ),
        )

        # Atualiza temáticas
        themes = _mangaupdates_themes(summary)
        if themes:
            self.replace_manga_themes(manga.id, themes)

        self._connection().commit()
        return True


    def confirm_mangaupdates_id(
        self,
        name: str,
        series_id,
        found_title: str | None = None,
    ) -> MangaUpdatesConfirmationResult:
        manga = self.find_by_normalized_title(name)
        if manga is None:
            return MangaUpdatesConfirmationResult(
                status="target_missing",
                series_id=_string_or_none(series_id),
                message="Obra local não encontrada para confirmar ID MangaUpdates.",
            )
        return self.confirm_mangaupdates_id_by_work_id(
            manga.id,
            series_id,
            found_title=found_title,
        )

    def confirm_mangaupdates_id_by_work_id(
        self,
        work_id,
        series_id,
        found_title: str | None = None,
    ) -> MangaUpdatesConfirmationResult:
        normalized_series_id = _string_or_none(series_id)
        target = self.find_by_id(work_id)
        if target is None:
            return MangaUpdatesConfirmationResult(
                status="target_missing",
                work_id=_int_or_none(work_id),
                series_id=normalized_series_id,
                message="Obra local não encontrada para confirmar ID MangaUpdates.",
            )

        existing = self.find_by_work_code(normalized_series_id)
        if existing is not None and _int_or_none(existing.id) != _int_or_none(target.id):
            return MangaUpdatesConfirmationResult(
                status="external_id_already_assigned",
                work_id=_int_or_none(target.id),
                series_id=normalized_series_id,
                existing_work_id=_int_or_none(existing.id),
                existing_title=existing.title,
                message="ID MangaUpdates já associado a outra obra.",
            )

        if str(target.work_code or "").strip() == str(normalized_series_id or "").strip():
            return MangaUpdatesConfirmationResult(
                status="already_applied",
                work_id=_int_or_none(target.id),
                series_id=normalized_series_id,
            )

        try:
            self._execute(
                """
                UPDATE mangas
                SET
                    work_code = %s,
                    alternative_title = COALESCE(
                        NULLIF(alternative_title, ''),
                        %s
                    )
                WHERE id = %s
                """,
                (
                    normalized_series_id,
                    _confirmation_alias(found_title, normalized_series_id),
                    target.id,
                ),
            )
            self._connection().commit()
        except Exception as exc:
            return MangaUpdatesConfirmationResult(
                status="persistence_error",
                work_id=_int_or_none(target.id),
                series_id=normalized_series_id,
                message=str(exc),
            )
        return MangaUpdatesConfirmationResult(
            status="applied",
            work_id=_int_or_none(target.id),
            series_id=normalized_series_id,
        )

    def correct_confirmed_mangaupdates_id(
        self,
        work_id,
        new_series_id,
        *,
        expected_current_work_code=None,
        event_message=None,
        event_payload=None,
    ) -> ConfirmedIdCorrectionResult:
        normalized_series_id = _string_or_none(new_series_id)
        expected_series_id = _string_or_none(expected_current_work_code)

        if not normalized_series_id:
            return ConfirmedIdCorrectionResult(
                status="invalid_id",
                work_id=_int_or_none(work_id),
                message="Informe um ID MangaUpdates válido.",
            )

        invalidated_fields = (
            "mangaupdates_url",
            "cover_url",
            "format",
            "latest_mangaupdates_chapter",
            "alternative_title",
        )
        try:
            target = self._find_by_id_for_update(work_id)
            if target is None:
                self._rollback_quietly()
                return ConfirmedIdCorrectionResult(
                    status="target_missing",
                    work_id=_int_or_none(work_id),
                    new_series_id=normalized_series_id,
                    expected_current_work_code=expected_series_id,
                    message="Obra local não encontrada para corrigir ID MangaUpdates.",
                )

            old_series_id = _string_or_none(target.work_code)
            if not old_series_id:
                self._rollback_quietly()
                return ConfirmedIdCorrectionResult(
                    status="missing_current_id",
                    work_id=_int_or_none(target.id),
                    new_series_id=normalized_series_id,
                    expected_current_work_code=expected_series_id,
                    actual_current_work_code=old_series_id,
                    message="A obra ainda não possui ID MangaUpdates confirmado.",
                )
            if expected_series_id and old_series_id != expected_series_id:
                self._rollback_quietly()
                return ConfirmedIdCorrectionResult(
                    status="stale_preview",
                    work_id=_int_or_none(target.id),
                    old_series_id=old_series_id,
                    new_series_id=normalized_series_id,
                    expected_current_work_code=expected_series_id,
                    actual_current_work_code=old_series_id,
                    message=(
                        "O ID confirmado desta obra foi alterado após o preview. "
                        "Faça uma nova validação antes de aplicar."
                    ),
                )
            if old_series_id == normalized_series_id:
                self._rollback_quietly()
                return ConfirmedIdCorrectionResult(
                    status="already_applied",
                    work_id=_int_or_none(target.id),
                    old_series_id=old_series_id,
                    new_series_id=normalized_series_id,
                    expected_current_work_code=expected_series_id,
                    actual_current_work_code=old_series_id,
                    message="A obra já está vinculada a este ID MangaUpdates.",
                )

            existing = self.find_by_work_code(normalized_series_id)
            if existing is not None and _int_or_none(existing.id) != _int_or_none(target.id):
                self._rollback_quietly()
                return ConfirmedIdCorrectionResult(
                    status="external_id_already_assigned",
                    work_id=_int_or_none(target.id),
                    old_series_id=old_series_id,
                    new_series_id=normalized_series_id,
                    existing_work_id=_int_or_none(existing.id),
                    existing_title=existing.title,
                    expected_current_work_code=expected_series_id,
                    actual_current_work_code=old_series_id,
                    message="ID MangaUpdates já associado a outra obra.",
                )

            self._execute(
                """
                UPDATE mangas
                SET
                    work_code = %s,
                    mangaupdates_url = NULL,
                    cover_url = NULL,
                    format = NULL,
                    latest_mangaupdates_chapter = NULL,
                    alternative_title = NULL,
                    notion_sync_status = %s
                WHERE id = %s
                """,
                (
                    normalized_series_id,
                    statuses.PENDING,
                    target.id,
                ),
            )
            self._execute(
                """
                DELETE FROM manga_themes
                WHERE manga_id = %s
                """,
                (target.id,),
            )
            self._execute(
                """
                INSERT INTO sync_events (
                    manga_id,
                    notion_page_id,
                    event_type,
                    sync_status,
                    message,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    target.id,
                    _string_or_none(getattr(target, "notion_page_id", None)),
                    "mangaupdates_confirmed_id_corrected",
                    statuses.PENDING,
                    event_message or "ID MangaUpdates confirmado corrigido.",
                    json.dumps({
                        "code": "mangaupdates_confirmed_id_corrected",
                        "old_work_code": old_series_id,
                        "new_work_code": normalized_series_id,
                        "invalidated_fields": list(invalidated_fields),
                        **(event_payload or {}),
                    }, ensure_ascii=False),
                ),
            )
            self._connection().commit()
        except Exception as exc:
            self._rollback_quietly()
            return ConfirmedIdCorrectionResult(
                status="persistence_error",
                work_id=_int_or_none(work_id),
                new_series_id=normalized_series_id,
                expected_current_work_code=expected_series_id,
                message=str(exc),
            )

        return ConfirmedIdCorrectionResult(
            status="applied",
            work_id=_int_or_none(target.id),
            old_series_id=old_series_id,
            new_series_id=normalized_series_id,
            invalidated_fields=invalidated_fields,
            notion_sync_status=statuses.PENDING,
            expected_current_work_code=expected_series_id,
            actual_current_work_code=old_series_id,
        )

    def _rollback_quietly(self):
        try:
            self._connection().rollback()
        except Exception:
            pass


    def update_notion_sync_fields(
        self,
        name: str,
        *,
        page_id=None,
        status=statuses.SYNCED,
        synced_at=None,
    ) -> bool:
        statuses.validate_status(status)
        manga = self._find_notion_match(name, page_id)
        if manga is None:
            return False

        self._execute(
            """
            UPDATE mangas
            SET
                notion_page_id = COALESCE(%s, notion_page_id),
                notion_last_synced_at = %s,
                notion_sync_status = %s
            WHERE id = %s
            """,
            (
                _string_or_none(page_id),
                synced_at or datetime.now().astimezone(),
                status,
                manga.id,
            ),
        )
        self._connection().commit()
        return True

    def update_notion_sync_fields_by_id(
        self,
        work_id: int,
        *,
        page_id=None,
        status=statuses.SYNCED,
        synced_at=None,
    ) -> bool:
        statuses.validate_status(status)
        self._execute(
            """
            UPDATE mangas
            SET
                notion_page_id = COALESCE(%s, notion_page_id),
                notion_last_synced_at = COALESCE(%s, notion_last_synced_at),
                notion_sync_status = %s
            WHERE id = %s
            """,
            (
                _string_or_none(page_id),
                synced_at,
                status,
                work_id,
            ),
        )
        self._connection().commit()
        return True

    def record_sync_event(
        self,
        name: str,
        *,
        event_type: str,
        status: str,
        page_id=None,
        message=None,
        payload=None,
    ) -> bool:
        statuses.validate_status(status)
        manga = self._find_notion_match(name, page_id)
        manga_id = manga.id if manga else None
        self._execute(
            """
            INSERT INTO sync_events (
                manga_id,
                notion_page_id,
                event_type,
                sync_status,
                message,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                manga_id,
                _string_or_none(page_id),
                event_type,
                status,
                message,
                json.dumps(payload or {}, ensure_ascii=False),
            ),
        )
        self._connection().commit()
        return True

    def record_sync_event_by_id(
        self,
        work_id: int,
        *,
        event_type: str,
        status: str,
        page_id=None,
        message=None,
        payload=None,
    ) -> bool:
        statuses.validate_status(status)
        self._execute(
            """
            INSERT INTO sync_events (
                manga_id,
                notion_page_id,
                event_type,
                sync_status,
                message,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                work_id,
                _string_or_none(page_id),
                event_type,
                status,
                message,
                json.dumps(payload or {}, ensure_ascii=False),
            ),
        )
        self._connection().commit()
        return True

    def enqueue_decision(
        self,
        *,
        decision_type: str,
        source: str,
        title: str,
        payload: dict,
        manga_name: str | None = None,
        source_key: str | None = None,
        status: str = "pending",
    ) -> bool:
        schema = self._decision_queue_schema()
        columns = set(schema)
        if not columns:
            return False

        type_column = _first_existing(columns, "decision_type", "type")
        title_column = _first_existing(
            columns,
            "title",
            "name",
            "manga_title",
            "work_title",
        )
        payload_column = _first_existing(columns, "payload", "data", "metadata")
        if not type_column or not title_column or not payload_column:
            return False

        row = {
            type_column: decision_type,
            title_column: title,
            payload_column: json.dumps(payload or {}, ensure_ascii=False),
        }
        optional = {
            "source": source,
            "status": status,
            "manga_name": manga_name or title,
            "source_key": source_key,
        }
        for column, value in optional.items():
            if column in columns and value not in (None, ""):
                row[column] = value

        existing_id = self._find_decision_id(
            columns,
            decision_type=decision_type,
            source=source,
            title=title,
            status=status,
        )
        if existing_id:
            assignments = ", ".join(
                f"{column} = {_placeholder_for(schema.get(column))}"
                for column in row
            )
            self._execute(
                f"""
                UPDATE decision_queue
                SET {assignments}
                WHERE id = %s
                """,
                (*row.values(), existing_id),
            )
            return True

        column_names = ", ".join(row)
        placeholders = ", ".join(
            _placeholder_for(schema.get(column)) for column in row
        )
        self._execute(
            f"""
            INSERT INTO decision_queue ({column_names})
            VALUES ({placeholders})
            """,
            tuple(row.values()),
        )
        return True

    def resolve_decision(
        self,
        *,
        decision_type: str,
        source: str,
        title: str,
        resolution: dict,
        status: str = "resolved",
    ) -> bool:
        schema = self._decision_queue_schema()
        columns = set(schema)
        if not columns:
            return False

        decision_id = self._find_decision_id(
            columns,
            decision_type=decision_type,
            source=source,
            title=title,
        )
        if not decision_id:
            return False

        values = {}
        if "status" in columns:
            values["status"] = status
        resolution_column = _first_existing(
            columns,
            "resolution",
            "decision",
            "resolved_payload",
        )
        if resolution_column:
            values[resolution_column] = json.dumps(
                resolution or {},
                ensure_ascii=False,
            )
        if "resolved_at" in columns:
            values["resolved_at"] = datetime.now().astimezone()
        if not values:
            return False

        assignments = ", ".join(
            f"{column} = {_placeholder_for(schema.get(column))}"
            for column in values
        )
        self._execute(
            f"""
            UPDATE decision_queue
            SET {assignments}
            WHERE id = %s
            """,
            (*values.values(), decision_id),
        )
        self._connection().commit()
        return True

    def mark_flow_id_candidates_applied(
        self,
        *,
        work_id: int | None = None,
        title: str | None = None,
        series_id: int | None = None,
        candidate_title: str | None = None,
    ) -> bool:
        if work_id is None and not title:
            return False

        clauses = ["status IN ('pending_review', 'not_found')"]
        params = []
        if work_id is not None and title:
            clauses.append("(work_id = %s OR searched_title = %s)")
            params.extend([work_id, title])
        elif work_id is not None:
            clauses.append("work_id = %s")
            params.append(work_id)
        else:
            clauses.append("searched_title = %s")
            params.append(title)

        details = {
            "applied": True,
            "applied_series_id": series_id,
            "applied_candidate_title": candidate_title,
        }
        self._execute(
            f"""
            UPDATE flow_id_candidates
            SET status = 'auto_matched',
                details = details || %s::jsonb
            WHERE {' AND '.join(clauses)}
            """,
            (json.dumps(details, ensure_ascii=False), *params),
        )
        self._connection().commit()
        return True

    def list_decisions(
        self,
        *,
        decision_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        schema = self._decision_queue_schema()
        columns = set(schema)
        if not columns:
            return []

        select_columns = [
            column for column in (
                "id",
                "decision_type",
                "type",
                "source",
                "source_key",
                "title",
                "name",
                "manga_title",
                "work_title",
                "payload",
                "data",
                "metadata",
                "resolution",
                "decision",
                "resolved_payload",
                "status",
                "created_at",
                "updated_at",
                "resolved_at",
            )
            if column in columns
        ]
        if not select_columns:
            return []

        type_column = _first_existing(columns, "decision_type", "type")
        clauses = []
        params = []
        if decision_type and type_column:
            clauses.append(f"{type_column} = %s")
            params.append(decision_type)
        if status and "status" in columns:
            clauses.append("status = %s")
            params.append(status)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order_column = "created_at" if "created_at" in columns else "id"
        rows = self._fetch_all(
            f"""
            SELECT {', '.join(select_columns)}
            FROM decision_queue
            {where}
            ORDER BY {order_column}, id
            """,
            tuple(params),
        )
        return [dict(row) for row in rows]

    def _fetch_all(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())

    def _fetch_one(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def _execute(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())

    def _cursor(self):
        return self._connection().cursor()

    def _connection(self):
        if self.connection is None:
            self.connection = self.connection_factory()
        return self.connection

    def _decision_queue_schema(self) -> dict[str, str]:
        rows = self._fetch_all(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'decision_queue'
            """
        )
        return {row["column_name"]: row.get("data_type", "") for row in rows}

    def _find_decision_id(
        self,
        columns,
        *,
        decision_type: str,
        source: str,
        title: str,
        status: str | None = None,
    ):
        type_column = _first_existing(columns, "decision_type", "type")
        title_column = _first_existing(
            columns,
            "title",
            "name",
            "manga_title",
            "work_title",
        )
        if not type_column or not title_column:
            return None

        clauses = [f"{type_column} = %s", f"{title_column} = %s"]
        params = [decision_type, title]
        if "source" in columns:
            clauses.append("source = %s")
            params.append(source)
        if status and "status" in columns:
            clauses.append("status = %s")
            params.append(status)

        row = self._fetch_one(
            f"""
            SELECT id
            FROM decision_queue
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            LIMIT 1
            """,
            tuple(params),
        )
        return row["id"] if row else None

    def _find_catalog_match(self, manga: dict) -> MangaRecord | None:
        work_code = _work_code(manga)
        if work_code:
            match = self.find_by_work_code(work_code)
            if match:
                return match
        return self.find_by_normalized_title(manga.get("nome", ""))

    def _find_notion_match(self, name: str, page_id=None) -> MangaRecord | None:
        if page_id:
            match = self.find_by_notion_page_id(str(page_id))
            if match:
                return match
        return self.find_by_normalized_title(name)

    def _insert_catalog_manga(self, manga: dict) -> int:
        row = self._fetch_one(
            """
            INSERT INTO mangas (
                work_code,
                title,
                alternative_title,
                reading_status_v2,
                personal_rank,
                last_read_chapter,
                latest_available_chapter,
                size_label,
                count_status,
                latest_mangaupdates_chapter,
                mangaupdates_url,
                cover_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                _work_code(manga),
                manga.get("nome"),
                _aliases(manga),
                "Quero Ler",
                "Normal",
                manga.get("ultimo_lido"),
                manga.get("main_caps"),
                manga.get("tamanho"),
                manga.get("count_status"),
                manga.get("mangaupdates_latest_chapter"),
                manga.get("mangaupdates_url"),
                manga.get("cover_url"),
            ),
        )
        return row["id"]

    def _update_catalog_manga(self, manga_id: int, manga: dict) -> None:
        self._execute(
            """
            UPDATE mangas
            SET
                work_code = COALESCE(work_code, %s),
                title = %s,
                alternative_title = COALESCE(NULLIF(alternative_title, ''), %s),
                last_read_chapter = COALESCE(last_read_chapter, %s),
                latest_available_chapter = %s,
                size_label = %s,
                count_status = %s,
                latest_mangaupdates_chapter = %s,
                mangaupdates_url = COALESCE(%s, mangaupdates_url),
                cover_url = COALESCE(%s, cover_url)
            WHERE id = %s
            """,
            (
                _work_code(manga),
                manga.get("nome"),
                _aliases(manga),
                manga.get("ultimo_lido"),
                manga.get("main_caps"),
                manga.get("tamanho"),
                manga.get("count_status"),
                manga.get("mangaupdates_latest_chapter"),
                manga.get("mangaupdates_url"),
                manga.get("cover_url"),
                manga_id,
            ),
        )
        self._connection().commit()


def _work_code(manga: dict):
    value = manga.get("work_code") or manga.get("mangaupdates_id")
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _aliases(manga: dict):
    aliases = manga.get("alias") or []
    if isinstance(aliases, str):
        return aliases.strip() or None
    cleaned = [str(alias).strip() for alias in aliases if str(alias).strip()]
    return " | ".join(cleaned) if cleaned else None


def _editorial_values(changes: dict):
    mapping = {
        "Status": ("reading_status_v2", _status_value),
        "Interesse": ("personal_rank", _rank_value),
        "Nota": ("score", _score_value),
        "Picância": ("spice_level", _plain_value),
        "Último lido": ("last_read_chapter", _plain_value),
        "Formato": ("format", _plain_value),
        "Alias": ("alternative_title", _plain_value),
    }
    values = {}
    for source, (target, transform) in mapping.items():
        if source in changes:
            values[target] = transform(changes[source])
    return values


def _theme_values(changes: dict):
    values = []
    for field in ("Temática", "Universo"):
        if field not in changes:
            continue
        values.extend(
            item.strip()
            for item in str(changes[field]).split("|")
            if item.strip()
        )
    return values or None


def _status_value(value):
    mapping = {
        "Quero ler": "Quero Ler",
        "Em espera": "Aguardando Atualização",
    }
    value = str(value or "").strip()
    return mapping.get(value, value)


def _rank_value(value):
    mapping = {
        "Topzera": "Topzera",
        "Legalzin": "Legalzin",
        "Despriorizado": "Despriorizado",
    }
    return mapping.get(str(value or "").strip(), "Normal")


def _score_value(value):
    mapping = {
        "Topzera": 10,
        "Legalzin": 8,
        "Ok": 6,
        "Meia boca": 4,
        "Ruim": 2,
    }
    value = str(value or "").strip()
    return mapping.get(value)


def _plain_value(value):
    value = str(value or "").strip()
    return value or None


def _string_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _confirmation_alias(value, series_id):
    alias = _empty_to_none(value)
    if alias is None:
        return None
    if _is_generated_id_alias(alias, series_id):
        return None
    return alias


def select_alternative_title(associated_titles, primary_title, work_code):
    if not isinstance(associated_titles, (list, tuple)):
        return None

    normalized_primary = normalize_title(primary_title)
    seen = set()
    for value in associated_titles:
        alias = _empty_to_none(value)
        if alias is None:
            continue
        alias_key = _alias_comparison_key(alias)
        if not alias_key or alias_key in seen:
            continue
        seen.add(alias_key)
        if normalized_primary and alias_key == normalized_primary:
            continue
        if _is_generated_id_alias(alias, work_code):
            continue
        return alias
    return None


def _alias_comparison_key(value):
    normalized = normalize_title(value)
    if normalized:
        return normalized
    return str(value or "").strip().casefold()


def _is_generated_id_alias(value, work_code):
    normalized_work_code = str(work_code or "").strip()
    if not normalized_work_code:
        return False
    return str(value or "").strip().casefold() == f"id {normalized_work_code}".casefold()


def _first_existing(columns, *candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _placeholder_for(data_type):
    if data_type == "jsonb":
        return "%s::jsonb"
    if data_type == "json":
        return "%s::json"
    return "%s"


def _empty_to_none(value):
    if value is None or str(value).strip() == "":
        return None
    return value


def _mangaupdates_themes(summary: dict):
    values = []
    for field in ("genres", "universe"):
        for value in summary.get(field, []) or []:
            if str(value or "").strip():
                values.append(str(value).strip())
    return values


def _normalize_ids(values):
    ordered = []
    seen = set()
    for value in values or ():
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number <= 0 or number in seen:
            continue
        ordered.append(number)
        seen.add(number)
    return ordered
