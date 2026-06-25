import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import mangaupdates
from manhwateca.mangaupdates_service.candidate_workflows import fill_ids_file


class FakeMangaRepository:
    def __init__(self):
        self.updated = []

    def update_mangaupdates_fields(self, name, series_id, summary):
        self.updated.append((name, series_id, summary))
        return True


class FakeDecisionRepository:
    def __init__(self):
        self.queued = []

    def enqueue_decision(self, **kwargs):
        self.queued.append(kwargs)
        return True


class MangaUpdatesTests(unittest.TestCase):
    def test_summarize_series_extracts_original_cover_url(self):
        summary = mangaupdates.summarize_series({
            "series_id": 123,
            "title": "Alpha",
            "image": {
                "url": {
                    "original": "https://cdn.example.test/original.jpg",
                    "thumb": "https://cdn.example.test/thumb.jpg",
                },
            },
        })

        self.assertEqual(
            "https://cdn.example.test/original.jpg",
            summary["cover_url"],
        )
        self.assertNotIn("thumbnail_url", summary)

    def test_choose_search_result_prefers_exact_manhwa(self):
        response = {
            "results": [
                {
                    "record": {
                        "series_id": 1,
                        "title": "Kiss Me if You Can",
                        "type": "Manhwa",
                    },
                    "hit_title": "Kiss Me if You Can",
                },
                {
                    "record": {
                        "series_id": 2,
                        "title": "Kiss Me if You Can (Novel)",
                        "type": "Novel",
                    },
                    "hit_title": "Kiss Me if You Can (Novel)",
                },
            ]
        }

        record, status = mangaupdates.choose_search_result(
            "Kiss Me If You Can",
            response,
        )

        self.assertEqual(1, record["series_id"])
        self.assertEqual("Exata (Manhwa)", status)

    def test_choose_search_result_rejects_ambiguous_exact_matches(self):
        response = {
            "results": [
                {
                    "record": {
                        "series_id": 1,
                        "title": "Alpha",
                        "type": "Novel",
                    },
                    "hit_title": "Alpha",
                },
                {
                    "record": {
                        "series_id": 2,
                        "title": "Alpha",
                        "type": "Novel",
                    },
                    "hit_title": "Alpha",
                },
            ]
        }

        record, status = mangaupdates.choose_search_result("Alpha", response)

        self.assertIsNone(record)
        self.assertEqual("Ambígua", status)

    def test_rank_search_results_handles_title_variations(self):
        response = {
            "results": [{
                "record": {
                    "series_id": 3923312591,
                    "title": "The Golden Goose Dressed as Alpha Boss",
                    "type": "Manhwa",
                    "genres": ["Yaoi"],
                    "year": "2025",
                    "url": "https://example.test/golden-goose",
                    "description": "A" * 800,
                },
            }]
        }

        candidates = mangaupdates.rank_search_results(
            "The Alpha's Golden Goose",
            response,
        )
        selected, status = mangaupdates.select_ranked_candidate(candidates)

        self.assertEqual(3923312591, selected["id"])
        self.assertEqual("Confirmado automaticamente", status)
        self.assertEqual(
            "https://example.test/golden-goose",
            candidates[0]["url"],
        )
        self.assertEqual(734, len(candidates[0]["descricao"]))
        self.assertTrue(candidates[0]["descricao"].endswith("…"))
        self.assertTrue(candidates[0]["bl"])

    def test_close_candidates_require_review(self):
        candidates = [
            {"id": 1, "pontuacao": 0.85, "posicao": 1},
            {"id": 2, "pontuacao": 0.82, "posicao": 2},
        ]

        selected, status = mangaupdates.select_ranked_candidate(candidates)

        self.assertIsNone(selected)
        self.assertEqual("Revisar", status)

    def test_multiple_plausible_title_variations_require_review(self):
        candidates = [
            {"id": 1, "pontuacao": 0.95, "posicao": 1},
            {"id": 2, "pontuacao": 0.725, "posicao": 2},
        ]

        selected, status = mangaupdates.select_ranked_candidate(candidates)

        self.assertIsNone(selected)
        self.assertEqual("Revisar", status)

    def test_unique_exact_match_is_confirmed_despite_strong_second(self):
        selected, status = mangaupdates.select_ranked_candidate([
            {"id": 1, "pontuacao": 1.0, "posicao": 1},
            {"id": 2, "pontuacao": 0.9, "posicao": 2},
        ])

        self.assertEqual(1, selected["id"])
        self.assertEqual("Confirmado automaticamente", status)

    def test_tied_exact_matches_still_require_review(self):
        selected, status = mangaupdates.select_ranked_candidate([
            {"id": 1, "pontuacao": 1.0, "posicao": 1},
            {"id": 2, "pontuacao": 1.0, "posicao": 2},
        ])

        self.assertIsNone(selected)
        self.assertEqual("Revisar", status)

    def test_candidate_filter_prefers_bl_and_supported_types(self):
        candidates = [
            {"id": 1, "tipo": "Manga", "bl": False},
            {"id": 2, "tipo": "Manhwa", "bl": True},
            {"id": 3, "tipo": "Novel", "bl": True},
        ]

        self.assertEqual(
            [2],
            [
                candidate["id"]
                for candidate in mangaupdates.filter_relevant_candidates(
                    candidates
                )
            ],
        )

    def test_short_description_is_whitespace_normalized(self):
        self.assertEqual(
            "Uma descrição curta.",
            mangaupdates.truncate_text("Uma\n descrição   curta."),
        )

    def test_fill_ids_removes_candidates_from_confirmed_items(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "busca_ids.json"
            path.write_text(
                json.dumps([{
                    "Nome": "Alpha",
                    "IDs": [{"id": 1, "titulo": "Alpha"}],
                    "Status": "Confirmado automaticamente",
                    "ID": 1,
                    "Nome encontrado": "Alpha",
                }]),
                encoding="utf-8",
            )

            items, processed = mangaupdates.fill_ids_file(
                path,
                limit=0,
                catalog_path=Path(directory) / "missing_catalog.json",
            )

            self.assertEqual(0, processed)
            self.assertNotIn("IDs", items[0])
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("IDs", persisted[0])

    def test_fill_ids_enqueues_review_candidates_in_decision_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "busca_ids.json"
            path.write_text(
                json.dumps([{"Nome": "Alpha"}]),
                encoding="utf-8",
            )
            queued = FakeDecisionRepository()

            items, processed = fill_ids_file(
                path,
                metadata={},
                search_candidates=lambda _item, _metadata, per_page=10: (
                    [{"id": 1, "titulo": "Alfa", "pontuacao": 0.7}],
                    "Alpha",
                ),
                save_function=lambda target, data: target.write_text(
                    json.dumps(data),
                    encoding="utf-8",
                ),
                wait_function=lambda _delay: None,
                limit=1,
                catalog_path=Path(directory) / "missing_catalog.json",
                decision_repository=queued,
            )

            self.assertEqual(1, processed)
            self.assertEqual("Revisar", items[0]["Status"])
            self.assertEqual(1, len(queued.queued))
            decision = queued.queued[0]
            self.assertEqual("mangaupdates_match", decision["decision_type"])
            self.assertEqual("mangaupdates", decision["source"])
            self.assertEqual("Alpha", decision["title"])
            self.assertEqual("Alpha", decision["payload"]["termo_busca"])

    def test_refresh_incomplete_candidates_only_reprocesses_missing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ids.json"
            path.write_text(
                json.dumps([
                    {
                        "Nome": "Incomplete",
                        "Status": "Revisar",
                        "IDs": [{"id": 1, "titulo": "Incomplete"}],
                    },
                    {
                        "Nome": "Complete",
                        "Status": "Revisar",
                        "IDs": [{
                            "id": 2,
                            "titulo": "Complete",
                            "url": "https://example.test",
                            "descricao": "Description",
                            "generos": ["Yaoi"],
                            "bl": True,
                        }],
                    },
                ]),
                encoding="utf-8",
            )
            response = {
                "results": [{
                    "record": {
                        "series_id": 1,
                        "title": "Incomplete",
                        "type": "Manhwa",
                        "url": "https://example.test/incomplete",
                        "description": "Now complete",
                        "genres": ["Yaoi"],
                    },
                }],
            }
            with mock.patch(
                "mangaupdates.search_series",
                return_value=response,
            ) as search:
                processed, pending = (
                    mangaupdates.refresh_incomplete_candidates(
                        path,
                        delay=0,
                        limit=10,
                    )
                )

            items = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            search.assert_called_once_with("Incomplete", per_page=10)
            self.assertEqual(
                "https://example.test/incomplete",
                items[0]["ID"] and response["results"][0]["record"]["url"],
            )
            self.assertEqual("Confirmado automaticamente", items[0]["Status"])
            self.assertNotIn("IDs", items[0])

    def test_refresh_incomplete_candidates_reprocesses_missing_bl_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ids.json"
            path.write_text(
                json.dumps([{
                    "Nome": "Exact Work",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 7,
                        "titulo": "Exact Work",
                        "url": "https://example.test/exact",
                        "descricao": "Description",
                    }],
                }]),
                encoding="utf-8",
            )
            response = {
                "results": [{
                    "record": {
                        "series_id": 7,
                        "title": "Exact Work",
                        "type": "Manhwa",
                        "url": "https://example.test/exact",
                        "description": "Description",
                        "genres": ["Shounen Ai"],
                    },
                }],
            }
            with mock.patch(
                "mangaupdates.search_series",
                return_value=response,
            ):
                processed, pending = (
                    mangaupdates.refresh_incomplete_candidates(
                        path,
                        delay=0,
                        limit=10,
                    )
                )

            item = json.loads(path.read_text(encoding="utf-8"))[0]
            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            self.assertEqual("Confirmado automaticamente", item["Status"])
            self.assertEqual(7, item["ID"])
            self.assertNotIn("IDs", item)

    def test_catalog_titles_are_added_to_id_searches(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog_path = Path(directory) / "mangas.json"
            catalog_path.write_text(
                json.dumps([
                    {"nome": "Obra existente"},
                    {"nome": "Obra nova"},
                ]),
                encoding="utf-8",
            )
            items = [{"Nome": "Obra Existente"}]

            added = mangaupdates.add_catalog_titles_to_id_searches(
                items,
                catalog_path=catalog_path,
            )

            self.assertEqual(1, added)
            self.assertEqual("Obra nova", items[-1]["Nome"])

    def test_search_terms_prefer_configured_alternatives(self):
        terms = mangaupdates.search_terms_for_item(
            {"Nome": "XX Cheio de Segredos"},
            {
                "XX Cheio de Segredos": {
                    "nome_oficial": "Full of Secrets",
                    "nomes_busca": ["The Secretive XX"],
                },
            },
        )

        self.assertEqual(
            ["The Secretive XX", "Full of Secrets", "XX Cheio de Segredos"],
            terms,
        )

    def test_search_candidates_uses_alternative_until_strong_match(self):
        responses = {
            "The Secretive XX": {
                "results": [{
                    "record": {
                        "series_id": 10,
                        "title": "The Secretive XX",
                        "type": "Manhwa",
                    },
                }],
            },
        }
        with mock.patch(
            "mangaupdates.search_series",
            side_effect=lambda title, per_page: responses[title],
        ) as search:
            candidates, term = mangaupdates.search_candidates_for_item(
                {"Nome": "XX Cheio de Segredos"},
                {
                    "XX Cheio de Segredos": {
                        "nomes_busca": ["The Secretive XX"],
                    },
                },
            )

        self.assertEqual("The Secretive XX", term)
        self.assertEqual(10, candidates[0]["id"])
        search.assert_called_once_with("The Secretive XX", per_page=10)

    def test_initial_filter_accepts_letters_accents_and_numbers(self):
        initial_filter = mangaupdates.normalize_initial_filter("AÇ 0-9")

        self.assertTrue(
            mangaupdates.matches_initial_filter("Além das memórias", initial_filter)
        )
        self.assertTrue(
            mangaupdates.matches_initial_filter("Ção", initial_filter)
        )
        self.assertTrue(mangaupdates.matches_initial_filter("2020", initial_filter))
        self.assertFalse(
            mangaupdates.matches_initial_filter("Beyond Memories", initial_filter)
        )

    def test_fetch_confirmed_details_skips_cached_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            cache_path = directory / "cache.json"
            ids_path.write_text(
                json.dumps([
                    {
                        "Nome": "Já consultada",
                        "Status": "Confirmado automaticamente",
                        "ID": 1,
                    },
                    {
                        "Nome": "Pendente",
                        "Status": "Confirmado automaticamente",
                        "ID": 2,
                    },
                ]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({"1": {"series_id": 1}}),
                encoding="utf-8",
            )

            with mock.patch(
                "mangaupdates.get_series",
                return_value={"series_id": 2, "title": "Pendente"},
            ) as get_series:
                processed, pending = mangaupdates.fetch_confirmed_details(
                    ids_path,
                    delay=0,
                    cache_path=cache_path,
                )

            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            get_series.assert_called_once_with(2)

    def test_fetch_confirmed_details_records_state(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            cache_path = directory / "cache.json"
            state_path = directory / "mangaupdates_state.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Pendente",
                    "Status": "Confirmado automaticamente",
                    "ID": 2,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text("{}", encoding="utf-8")

            with mock.patch(
                "mangaupdates.get_series",
                return_value={"series_id": 2, "title": "Pendente"},
            ):
                processed, pending = mangaupdates.fetch_confirmed_details(
                    ids_path,
                    delay=0,
                    cache_path=cache_path,
                    state_path=state_path,
                )

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            self.assertEqual("cache_valido", state["series"]["2"]["status"])
            self.assertIn("last_checked_at", state["series"]["2"])

    def test_fetch_confirmed_details_refreshes_expired_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            cache_path = directory / "cache.json"
            state_path = directory / "mangaupdates_state.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Expirada",
                    "Status": "Confirmado automaticamente",
                    "ID": 7,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({"7": {"series_id": 7, "title": "Antiga"}}),
                encoding="utf-8",
            )
            state_path.write_text(
                json.dumps({
                    "series": {
                        "7": {
                            "last_checked_at": "2020-01-01T00:00:00+00:00",
                            "status": "cache_valido",
                        }
                    }
                }),
                encoding="utf-8",
            )

            with mock.patch(
                "mangaupdates.get_series",
                return_value={"series_id": 7, "title": "Nova"},
            ) as get_series:
                processed, pending = mangaupdates.fetch_confirmed_details(
                    ids_path,
                    delay=0,
                    cache_path=cache_path,
                    state_path=state_path,
                    ttl_days=30,
                )

            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            self.assertEqual("Nova", cache["7"]["title"])
            get_series.assert_called_once_with(7)

    def test_fetch_confirmed_details_force_refreshes_cached_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            cache_path = directory / "cache.json"
            state_path = directory / "mangaupdates_state.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Cache existente",
                    "Status": "Confirmado automaticamente",
                    "ID": 8,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({"8": {"series_id": 8, "title": "Antiga"}}),
                encoding="utf-8",
            )
            state_path.write_text(
                json.dumps({
                    "series": {
                        "8": {
                            "last_checked_at": "2099-01-01T00:00:00+00:00",
                            "status": "cache_valido",
                        }
                    }
                }),
                encoding="utf-8",
            )

            with mock.patch(
                "mangaupdates.get_series",
                return_value={"series_id": 8, "title": "Forçada"},
            ) as get_series:
                processed, pending = mangaupdates.fetch_confirmed_details(
                    ids_path,
                    delay=0,
                    cache_path=cache_path,
                    state_path=state_path,
                    force_refresh=True,
                )

            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            self.assertEqual(1, processed)
            self.assertEqual(0, pending)
            self.assertEqual("Forçada", cache["8"]["title"])
            get_series.assert_called_once_with(8)

    def test_update_csv_from_confirmed_ids_preserves_editorial_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Dear Romantic Captain",
                    "Status": "Confirmado automaticamente",
                    "ID": 21459838347,
                    "Nome encontrado": "Romantic Captain Darling",
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({
                    "21459838347": {
                        "series_id": 21459838347,
                        "latest_chapter": "66",
                        "url": "https://example.test/captain",
                        "genres": ["Drama", "Yaoi"],
                        "format": "Manhwa",
                        "universe": [],
                    },
                }),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({
                    "Nome": "Dear Romantic Captain",
                    "Alias": "Querido Capitão Romântico",
                    "Interesse": "Fila de Espera",
                    "Status": "Quero ler",
                    "Nota": "Ok",
                })

            updated, checked, uncached, missing_from_csv = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    delay=0,
                )
            )

            with csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                row = next(csv.DictReader(file))
            self.assertEqual(1, updated)
            self.assertEqual(1, checked)
            self.assertEqual([], uncached)
            self.assertEqual([], missing_from_csv)
            self.assertEqual("Fila de Espera", row["Interesse"])
            self.assertEqual("Quero ler", row["Status"])
            self.assertEqual("Ok", row["Nota"])
            self.assertEqual("21459838347", row["ID da obra"])
            self.assertEqual("66", row["Capítulo MangaUpdates"])
            self.assertEqual(
                "ID confirmado automaticamente",
                row["Correspondência API"],
            )

    def test_update_csv_persists_mangaupdates_data_to_database(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            repository = FakeMangaRepository()
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Beyond Memories",
                    "Status": "Confirmado manualmente",
                    "ID": 46829042951,
                }]),
                encoding="utf-8",
            )
            summary = {
                "series_id": 46829042951,
                "latest_chapter": 104,
                "url": "https://example.test/beyond",
                "genres": ["Drama"],
                "format": "Manhwa",
                "universe": ["Omegaverse"],
            }
            cache_path.write_text(
                json.dumps({"46829042951": summary}),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({"Nome": "Beyond Memories"})

            mangaupdates.update_csv_from_confirmed_ids(
                ids_path,
                csv_path=csv_path,
                cache_path=cache_path,
                delay=0,
                database_repository=repository,
            )

            self.assertEqual(
                [("Beyond Memories", 46829042951, summary)],
                repository.updated,
            )

    def test_update_csv_distinguishes_uncached_from_missing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            ids_path.write_text(
                json.dumps([
                    {
                        "Nome": "Sem cache",
                        "Status": "Confirmado automaticamente",
                        "ID": 1,
                    },
                    {
                        "Nome": "Fora do CSV",
                        "Status": "Confirmado automaticamente",
                        "ID": 2,
                    },
                ]),
                encoding="utf-8",
            )
            cache_path.write_text("{}", encoding="utf-8")
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({"Nome": "Sem cache"})

            updated, checked, uncached, missing_from_csv = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    delay=0,
                )
            )

            self.assertEqual(0, updated)
            self.assertEqual(0, checked)
            self.assertEqual(["Sem cache"], uncached)
            self.assertEqual(["Fora do CSV"], missing_from_csv)

    def test_update_csv_appends_catalog_row_when_confirmed_id_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            catalog_path = directory / "mangas.json"
            metadata_path = directory / "metadata.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "The Trapped Beast",
                    "Status": "Confirmado manualmente",
                    "ID": 15541779211,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({
                    "15541779211": {
                        "series_id": 15541779211,
                        "latest_chapter": 28,
                        "url": "https://example.test/the-trapped-beast",
                        "format": "Manhua",
                        "genres": ["Yaoi"],
                        "universe": [],
                    },
                }),
                encoding="utf-8",
            )
            catalog_path.write_text(
                json.dumps([{
                    "nome": "The Trapped Beast",
                    "alias": [],
                    "status": "Quero ler",
                    "nota": "Ok",
                    "main_caps": 28,
                    "chapters_found": 30,
                    "side_stories_found": 0,
                    "count_status": "OK",
                }]),
                encoding="utf-8",
            )
            metadata_path.write_text("{}", encoding="utf-8")
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()

            updated, checked, uncached, missing_from_csv = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    catalog_path=catalog_path,
                    delay=0,
                )
            )

            with csv_path.open(encoding="utf-8-sig", newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(1, updated)
            self.assertEqual(1, checked)
            self.assertEqual([], uncached)
            self.assertEqual([], missing_from_csv)
            self.assertEqual("The Trapped Beast", row["Nome"])
            self.assertEqual("15541779211", row["ID da obra"])
            self.assertEqual("28", row["Capítulo MangaUpdates"])

    def test_manual_confirmation_is_exported_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Beyond Memories",
                    "Status": "Confirmado manualmente",
                    "ID": 46829042951,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({
                    "46829042951": {
                        "series_id": 46829042951,
                        "url": "https://example.test/beyond",
                    },
                }),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({"Nome": "Beyond Memories"})

            updated, checked, uncached, missing = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    delay=0,
                )
            )

            with csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                row = next(csv.DictReader(file))
            self.assertEqual(1, updated)
            self.assertEqual(1, checked)
            self.assertEqual([], uncached)
            self.assertEqual([], missing)
            self.assertEqual(
                "ID confirmado manualmente",
                row["Correspondência API"],
            )

    def test_update_csv_deduplicates_same_id_and_matches_catalog_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "busca_ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            metadata_path = directory / "catalog_metadata.json"
            ids_path.write_text(
                json.dumps([
                    {
                        "Nome": "Love Shuttle",
                        "Status": "Confirmado manualmente",
                        "ID": 53840259364,
                    },
                    {
                        "Nome": "Ônibus do amor_love shuttle",
                        "Status": "Confirmado manualmente",
                        "ID": 53840259364,
                    },
                ]),
                encoding="utf-8",
            )
            cache_path.write_text("{}", encoding="utf-8")
            metadata_path.write_text(
                json.dumps({
                    "Ônibus do amor_love shuttle": {
                        "nome_oficial": "Love Shuttle",
                        "alias": "Ônibus do Amor",
                    },
                }),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({
                    "Nome": "Love Shuttle",
                    "Alias": "Ônibus do Amor",
                })

            with mock.patch.object(
                mangaupdates,
                "METADATA_FILE",
                metadata_path,
            ):
                updated, checked, uncached, missing = (
                    mangaupdates.update_csv_from_confirmed_ids(
                        ids_path,
                        csv_path=csv_path,
                        cache_path=cache_path,
                        delay=0,
                    )
                )

            self.assertEqual(0, updated)
            self.assertEqual(0, checked)
            self.assertEqual(["Love Shuttle"], uncached)
            self.assertEqual([], missing)

    def test_update_csv_does_not_count_unchanged_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "2020",
                    "Status": "Confirmado manualmente",
                    "ID": 8230323430,
                }]),
                encoding="utf-8",
            )
            cache_path.write_text(
                json.dumps({
                    "8230323430": {
                        "series_id": 8230323430,
                        "latest_chapter": 62,
                        "url": "https://example.test/2020",
                        "genres": ["Drama"],
                        "format": "Manhwa",
                        "universe": [],
                    },
                }),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({
                    "Nome": "2020",
                    "ID da obra": 8230323430,
                    "Capítulo MangaUpdates": 62,
                    "MangaUpdates": "https://example.test/2020",
                    "Temática": "Drama",
                    "Formato": "Manhwa",
                    "Universo": "",
                    "Correspondência API": "ID confirmado manualmente",
                })

            updated, checked, uncached, missing = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    delay=0,
                )
            )

            self.assertEqual(0, updated)
            self.assertEqual(1, checked)
            self.assertEqual([], uncached)
            self.assertEqual([], missing)

    def test_update_csv_marks_rows_missing_from_catalog_as_orphan(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "ids.json"
            csv_path = directory / "catalog.csv"
            cache_path = directory / "cache.json"
            catalog_path = directory / "mangas.json"
            ids_path.write_text("[]", encoding="utf-8")
            cache_path.write_text("{}", encoding="utf-8")
            catalog_path.write_text(
                json.dumps([{"nome": "Alpha", "alias": []}]),
                encoding="utf-8",
            )
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=mangaupdates.CSV_COLUMNS,
                )
                writer.writeheader()
                writer.writerow({
                    "Nome": "Alpha",
                    "Correspondência API": "ID confirmado manualmente",
                })
                writer.writerow({
                    "Nome": "Removed Work",
                    "Correspondência API": "ID confirmado manualmente",
                })

            updated, checked, uncached, missing = (
                mangaupdates.update_csv_from_confirmed_ids(
                    ids_path,
                    csv_path=csv_path,
                    cache_path=cache_path,
                    catalog_path=catalog_path,
                    delay=0,
                )
            )

            with csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(1, updated)
            self.assertEqual(0, checked)
            self.assertEqual([], uncached)
            self.assertEqual([], missing)
            self.assertEqual(
                "ID confirmado manualmente",
                rows[0]["Correspondência API"],
            )
            self.assertEqual(
                "Fora do catálogo local",
                rows[1]["Correspondência API"],
            )

    def test_write_csv_uses_notion_columns_and_id(self):
        manga = {
            "nome": "Alpha",
            "alias": [],
            "interesse": "Muito alto",
            "status": "Quero ler",
            "nota": "Ok",
            "ultimo_lido": 0,
            "main_caps": 10,
            "chapters_found": 8,
            "side_stories_found": 2,
            "count_status": "Revisar",
        }
        external = {
            "series_id": 123,
            "url": "https://example.test/alpha",
            "latest_chapter": 11,
            "format": "Manhwa",
            "genres": ["Drama"],
            "universe": ["Fantasia"],
            "associated_titles": ["A"],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.csv"
            mangaupdates.write_csv(
                [manga],
                {"Alpha": external},
                {"Alpha": {"match_status": "Exata"}},
                path,
                metadata_path=Path(directory) / "missing.json",
            )
            with path.open(encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                row = next(reader)

        self.assertEqual(
            ["ID da obra", "Nome", "Alias", "Interesse"],
            reader.fieldnames[:4],
        )
        self.assertEqual("123", row["ID da obra"])
        self.assertEqual("Muito alto", row["Interesse"])
        self.assertEqual("Drama", row["Temática"])
        self.assertEqual("Exata", row["Correspondência API"])

    def test_catalog_metadata_overrides_name_alias_and_interest(self):
        row = mangaupdates.build_csv_row(
            {"nome": "Nome local", "alias": [], "interesse": ""},
            metadata={
                "nome_oficial": "Official Name",
                "alias": "Nome em Português",
                "interesse": "Topzera",
            },
        )

        self.assertEqual("Official Name", row["Nome"])
        self.assertEqual("Nome em Português", row["Alias"])
        self.assertEqual("Topzera", row["Interesse"])

    def test_portuguese_alias_replaces_external_aliases(self):
        row = mangaupdates.build_csv_row(
            {"nome": "Local", "alias": ["Alias local"]},
            external={"associated_titles": ["Alias externo"]},
            metadata={"alias": "Nome em Português"},
        )

        self.assertEqual("Nome em Português", row["Alias"])

    def test_enrich_catalog_reuses_confirmed_cache_without_api_calls(self):
        manga = {"nome": "Alpha"}
        cached = {"series_id": 123, "title": "Alpha"}

        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "progress.json"
            cache_path = Path(directory) / "cache.json"
            cache_path.write_text(
                json.dumps({"Alpha": cached}),
                encoding="utf-8",
            )
            progress, _cache = mangaupdates.enrich_catalog(
                [manga],
                delay=0,
                progress_path=progress_path,
                cache_path=cache_path,
            )

        self.assertEqual("Cache confirmado", progress["Alpha"]["match_status"])
        self.assertEqual(123, progress["Alpha"]["series_id"])
