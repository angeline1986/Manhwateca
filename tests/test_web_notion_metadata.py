import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from manhwateca.notion_sync.csv_status import write_csv_status
from manhwateca.webapp.notion_metadata import metadata_status
from manhwateca.webapp.notion_pages import create_missing_page_payload
from manhwateca.webapp.notion_sync_candidates import sync_candidates_payload


class WebNotionMetadataTests(unittest.TestCase):
    def test_status_writer_and_web_payload_include_preview(self):
        summary = {
            "updated": 1,
            "updates": [{
                "name": "Alpha",
                "properties": ["Alias", "ID da obra", "MangaUpdates"],
            }],
            "missing": ["Beta"],
            "duplicates": ["Gamma"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "reports/integrations/manhwateca_import.csv"
            csv_path.parent.mkdir(parents=True)
            csv_path.write_text("Nome\nAlpha\n", encoding="utf-8")
            status_path = (
                root / "reports/integrations/notion_csv_status.json"
            )
            write_csv_status(
                summary,
                False,
                status_path,
                source={"kind": "postgresql", "label": "PostgreSQL"},
            )
            sync_path = root / "reports/integrations/sync_state.json"
            sync_path.write_text(
                json.dumps({
                    "updated_at": "2026-06-17T10:00:00-03:00",
                    "works": {
                        "Alpha": {"status": "sincronizado"},
                        "Beta": {"status": "pendente"},
                    },
                }),
                encoding="utf-8",
            )

            payload = metadata_status(root)

        self.assertTrue(payload["available"])
        self.assertTrue(payload["csv_available"])
        self.assertEqual("SIMULAÇÃO", payload["mode"])
        self.assertEqual("postgresql", payload["source"]["kind"])
        self.assertEqual("PostgreSQL", payload["source"]["label"])
        self.assertEqual(1, payload["summary"]["updates"])
        self.assertEqual(["Beta"], payload["missing"])
        self.assertEqual(
            ["Alias", "ID da obra", "MangaUpdates"],
            payload["updates"][0]["properties"],
        )
        self.assertIn("sync", payload)
        self.assertEqual("legacy_report", payload["sync"]["evidence"])
        self.assertFalse(payload["sync"]["validated_against_notion"])
        self.assertEqual("Relatório legado", payload["sync"]["source_label"])
        self.assertEqual("blocked", payload["sync"]["status"])
        self.assertEqual("review_duplicates", payload["sync"]["next_action"])
        self.assertEqual(1, payload["sync"]["updated_count"])
        self.assertEqual(1, payload["sync"]["missing_count"])
        self.assertEqual(1, payload["sync"]["duplicate_count"])
        self.assertEqual(
            ["missing_page", "duplicate_page"],
            [blocker["code"] for blocker in payload["sync"]["blockers"]],
        )
        self.assertTrue(payload["sync_state"]["available"])
        self.assertEqual(2, payload["sync_state"]["total"])
        self.assertEqual(
            1,
            payload["sync_state"]["statuses"]["sincronizado"],
        )

    def test_status_includes_synced_sync_result(self):
        payload = self._metadata_payload({
            "updated": 0,
            "updates": [],
            "unchanged": ["Alpha"],
            "missing": [],
            "duplicates": [],
        })

        self.assertTrue(payload["available"])
        self.assertEqual("legacy_report", payload["sync"]["evidence"])
        self.assertFalse(payload["sync"]["validated_against_notion"])
        self.assertEqual("Relatório legado", payload["sync"]["source_label"])
        self.assertEqual("synced", payload["sync"]["status"])
        self.assertEqual("none", payload["sync"]["next_action"])
        self.assertEqual(1, payload["sync"]["unchanged_count"])
        self.assertEqual([], payload["sync"]["blockers"])

    def test_status_includes_paused_sync_result(self):
        payload = self._metadata_payload({
            "updated": 2,
            "updates": [{"name": "Alpha"}, {"name": "Beta"}],
            "unchanged": [],
            "missing": [],
            "duplicates": [],
        })

        self.assertEqual("paused", payload["sync"]["status"])
        self.assertEqual("apply", payload["sync"]["next_action"])
        self.assertEqual(2, payload["sync"]["updated_count"])
        self.assertEqual([], payload["sync"]["blockers"])

    def test_status_includes_error_sync_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_csv_status.json"
            path.parent.mkdir(parents=True)
            path.write_text("{invalid", encoding="utf-8")

            payload = metadata_status(root)

        self.assertFalse(payload["available"])
        self.assertIn("inválido", payload["error"])
        self.assertEqual("error", payload["sync"]["status"])
        self.assertEqual("retry", payload["sync"]["next_action"])
        self.assertEqual("unavailable", payload["sync"]["evidence"])
        self.assertFalse(payload["sync"]["validated_against_notion"])
        self.assertEqual("Indisponível", payload["sync"]["source_label"])
        self.assertEqual("api_error", payload["sync"]["blockers"][0]["code"])
        self.assertIn("inválido", payload["sync"]["blockers"][0]["message"])

    def test_invalid_status_has_safe_empty_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_csv_status.json"
            path.parent.mkdir(parents=True)
            path.write_text("{invalid", encoding="utf-8")

            payload = metadata_status(root)

        self.assertFalse(payload["available"])
        self.assertIn("inválido", payload["error"])
        self.assertIn("sync", payload)

    def test_missing_status_keeps_legacy_empty_response(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = metadata_status(Path(directory))

        self.assertFalse(payload["available"])
        self.assertFalse(payload["csv_available"])
        self.assertEqual(
            {"updates": 0, "unchanged": 0, "missing": 0, "duplicates": 0},
            payload["summary"],
        )
        self.assertEqual([], payload["updates"])
        self.assertEqual([], payload["unchanged"])
        self.assertEqual([], payload["missing"])
        self.assertEqual([], payload["duplicates"])
        self.assertIsNone(payload["sync"])
        self.assertIsNone(payload["error"])

    def test_sync_candidates_default_queue_excludes_synced_and_review_items(self):
        payload = sync_candidates_payload(repository=FakeCandidateRepository([
            candidate(259, "Dressed_to_Kill", work_code="38551408461"),
            candidate(261, "Pendente", status="pending"),
            candidate(262, "Erro", status="error"),
            candidate(260, "Sem ID", work_code=None),
            candidate(4, "A Seducao da Serpente", status="synced"),
            candidate(5, "Duplicada", status="conflict"),
            candidate(6, "Ignorada", status="ignored"),
        ]))

        self.assertEqual("default", payload["filter"])
        self.assertEqual(6, payload["summary"]["total"])
        self.assertEqual(1, payload["summary"]["neverSynced"])
        self.assertEqual(1, payload["summary"]["synced"])
        self.assertEqual(1, payload["summary"]["pending"])
        self.assertEqual(1, payload["summary"]["error"])
        self.assertEqual(1, payload["summary"]["conflict"])
        titles = [item["title"] for item in payload["items"]]
        self.assertEqual(["Dressed_to_Kill", "Pendente", "Erro"], titles)
        self.assertNotIn("A Seducao da Serpente", titles)
        self.assertNotIn("Duplicada", titles)
        self.assertNotIn("Ignorada", titles)
        dressed = next(
            item for item in payload["items"]
            if item["title"] == "Dressed_to_Kill"
        )
        self.assertEqual(259, dressed["workId"])
        self.assertEqual("Nunca sincronizada", dressed["displayStatus"])
        self.assertTrue(dressed["selectable"])

    def test_sync_candidates_synced_filter_shows_synced_items(self):
        payload = sync_candidates_payload(
            "status=synced",
            repository=FakeCandidateRepository([
                candidate(1, "2020", status="synced", page_id="page-id"),
                candidate(2, "Pendente", status="pending"),
            ]),
        )

        self.assertEqual("synced", payload["filter"])
        self.assertEqual(2, payload["summary"]["total"])
        self.assertEqual(["2020"], [item["title"] for item in payload["items"]])
        self.assertEqual("Sincronizada", payload["items"][0]["displayStatus"])
        self.assertTrue(payload["items"][0]["selectable"])

    def test_sync_candidates_invalid_filter_uses_default_queue(self):
        payload = sync_candidates_payload(
            "status=invalido",
            repository=FakeCandidateRepository([
                candidate(1, "Nunca", status=None),
                candidate(2, "Sincronizada", status="synced"),
            ]),
        )

        self.assertEqual("default", payload["filter"])
        self.assertEqual(["Nunca"], [item["title"] for item in payload["items"]])

    def test_sync_candidates_mark_conflict_as_review_not_normal_selection(self):
        payload = sync_candidates_payload(
            "status=all",
            repository=FakeCandidateRepository([
                candidate(5, "Duplicada", work_code="123", status="conflict"),
            ]),
        )

        item = payload["items"][0]
        self.assertEqual("Precisa de revisão", item["displayStatus"])
        self.assertFalse(item["selectable"])

    def test_create_missing_page_payload_creates_only_missing_page(self):
        repository = FakeNotionPageRepository([
            candidate(
                254,
                "Mad for love",
                work_code="123",
                alternative_title="Mad Love",
            ),
        ])
        notion = FakeNotionForCreate(database_pages=[], created_page={"id": "page-new"})

        payload, status = create_missing_page_payload(
            {"work_id": 254},
            notion=notion,
            database_id="database-id",
            repository=repository,
        )

        self.assertEqual(201, status)
        self.assertEqual("synced", payload["sync"]["status"])
        self.assertEqual(1, payload["sync"]["applied_count"])
        self.assertEqual(1, len(notion.pages.created))
        create_payload = notion.pages.created[0]
        self.assertEqual({"database_id": "database-id"}, create_payload["parent"])
        self.assertEqual(
            {"title": [{"text": {"content": "Mad for love"}}]},
            create_payload["properties"]["Nome"],
        )
        self.assertEqual({"number": 123}, create_payload["properties"]["ID da obra"])
        self.assertEqual(
            {"rich_text": [{"text": {"content": "Mad Love"}}]},
            create_payload["properties"]["Alias"],
        )
        self.assertEqual("page-new", repository.updated[0]["page_id"])
        self.assertEqual(1, len(repository.events))

    def test_create_missing_page_payload_refuses_when_page_exists(self):
        repository = FakeNotionPageRepository([
            candidate(254, "Mad for love", work_code="123"),
        ])
        notion = FakeNotionForCreate(database_pages=[
            notion_page("Mad for love", "page-existing"),
        ])

        payload, status = create_missing_page_payload(
            {"work_id": 254},
            notion=notion,
            database_id="database-id",
            repository=repository,
        )

        self.assertEqual(409, status)
        self.assertIn("error", payload)
        self.assertEqual([], notion.pages.created)
        self.assertEqual([], repository.updated)
        self.assertEqual([], repository.events)

    def _metadata_payload(self, summary):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_path = (
                root / "reports/integrations/notion_csv_status.json"
            )
            write_csv_status(
                summary,
                False,
                status_path,
                source={"kind": "postgresql", "label": "PostgreSQL"},
            )
            return metadata_status(root)


class FakeCandidateRepository:
    def __init__(self, records):
        self.records = records
        self.list_calls = 0

    def list_mangas(self):
        self.list_calls += 1
        return self.records


class FakeNotionPageRepository(FakeCandidateRepository):
    def __init__(self, records):
        super().__init__(records)
        self.updated = []
        self.events = []

    def find_by_id(self, work_id):
        return next((record for record in self.records if record.id == work_id), None)

    def list_mangas_by_ids(self, work_ids):
        wanted = {int(work_id) for work_id in work_ids}
        return [record for record in self.records if int(record.id) in wanted]

    def update_notion_sync_fields_by_id(self, work_id, **kwargs):
        self.updated.append({"work_id": work_id, **kwargs})
        return True

    def record_sync_event_by_id(self, work_id, **kwargs):
        self.events.append({"work_id": work_id, **kwargs})
        return True


class FakeNotionForCreate:
    def __init__(self, database_pages=None, created_page=None):
        self.databases = SimpleNamespace(
            query=lambda **_kwargs: {"results": database_pages or [], "has_more": False}
        )
        self.pages = FakeCreatePages(created_page or {"id": "page-new"})


class FakeCreatePages:
    def __init__(self, created_page):
        self.created_page = created_page
        self.created = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return self.created_page

    def retrieve(self, **kwargs):
        raise AssertionError("retrieve should not be called for missing page")


def candidate(
    work_id,
    title,
    *,
    work_code="123",
    status=None,
    synced_at=None,
    page_id=None,
    alternative_title=None,
):
    return SimpleNamespace(
        id=work_id,
        title=title,
        work_code=work_code,
        alternative_title=alternative_title,
        latest_mangaupdates_chapter=None,
        mangaupdates_url="https://example.test/work",
        themes=[],
        format=None,
        cover_url="https://example.test/cover.jpg",
        notion_page_id=page_id,
        notion_sync_status=status,
        notion_last_synced_at=synced_at,
    )


def notion_page(title, page_id):
    return {
        "id": page_id,
        "last_edited_time": "2026-01-01T00:00:00.000Z",
        "properties": {
            "Nome": {"type": "title", "title": [{"plain_text": title}]},
        },
    }
