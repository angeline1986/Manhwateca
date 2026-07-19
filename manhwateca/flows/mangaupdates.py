from concurrent.futures import ThreadPoolExecutor, TimeoutError

from manhwateca.database.manga_repository import MangaRepository
from manhwateca.flows.domain import FlowMessage, Progress, StageId
from manhwateca.flows.integrations import (
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    MetadataUpdateResult,
    SeriesSearchResult,
)
from manhwateca.flows.repository import (
    FlowRepository,
    IdCandidateRecord,
)
from manhwateca.mangaupdates_service.client import search_series
from manhwateca.mangaupdates_service.matching import (
    filter_relevant_candidates,
    rank_search_results,
    select_ranked_candidate,
)


class MangaUpdatesFlowIntegration:
    def __init__(
        self,
        *,
        flow_repository_factory=FlowRepository,
        manga_repository_factory=MangaRepository,
        search_function=search_series,
        per_page: int = 5,
        timeout: int = 8,
        retries: int = 0,
    ):
        self.flow_repository_factory = flow_repository_factory
        self.manga_repository_factory = manga_repository_factory
        self.search_function = search_function
        self.per_page = per_page
        self.timeout = timeout
        self.retries = retries

    def check_status(self) -> IntegrationCheck:
        return IntegrationCheck(
            "MangaUpdates",
            IntegrationStatus.OPERATIONAL,
            message="Integração MangaUpdates disponível para resolução de IDs.",
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        return IntegrationValidation(stage=stage, valid=True)

    def search_series(self) -> SeriesSearchResult:
        flow_repository = self.flow_repository_factory()
        execution = flow_repository.latest_execution()
        if execution is None or execution.execution_id is None:
            raise RuntimeError("Nenhum Workflow iniciado para resolver IDs.")

        works = flow_repository.list_catalog_works_for_id_resolution()
        eligible = [work for work in works if not str(work.work_code or "").strip()]
        already_resolved = len(works) - len(eligible)
        manga_repository = self.manga_repository_factory()
        matched = 0
        pending = 0
        not_found = 0
        errors = 0

        flow_repository.clear_id_candidates(execution.execution_id)
        flow_repository.append_message(
            execution.execution_id,
            StageId.RESOLVE_IDS,
            "info",
            FlowMessage(
                "Resolução de IDs iniciada.",
                details={
                    "eligible": len(eligible),
                    "alreadyResolved": already_resolved,
                },
            ),
        )
        flow_repository.update_stage_progress(
            execution.execution_id,
            StageId.RESOLVE_IDS,
            Progress(current=0, total=len(eligible)),
        )
        for work in eligible:
            processed = matched + pending
            flow_repository.update_stage_progress(
                execution.execution_id,
                StageId.RESOLVE_IDS,
                Progress(current=processed, total=len(eligible)),
                current_item=work.title,
            )
            flow_repository.append_log(
                _log(
                    execution.execution_id,
                    "mangaupdates_search_start",
                    "running",
                    f"Consultando MangaUpdates para {work.title}.",
                    {"workId": work.work_id, "title": work.title},
                )
            )
            try:
                response = _search_with_deadline(
                    self.search_function,
                    work.title,
                    self.timeout,
                    {
                        "per_page": self.per_page,
                        "timeout": self.timeout,
                        "retries": self.retries,
                    },
                )
                ranked = filter_relevant_candidates(
                    rank_search_results(work.title, response)
                )[:self.per_page]
                selected, status = select_ranked_candidate(ranked)
                if selected:
                    manga_repository.confirm_mangaupdates_id(
                        work.title,
                        selected["id"],
                        selected.get("titulo"),
                    )
                    _commit_repository(manga_repository)
                    flow_repository.append_id_candidate(_candidate_record(
                        execution.execution_id,
                        work.work_id,
                        work.title,
                        selected,
                        "auto_matched",
                        {"selectionStatus": status},
                    ))
                    matched += 1
                elif ranked:
                    for candidate in ranked:
                        flow_repository.append_id_candidate(_candidate_record(
                            execution.execution_id,
                            work.work_id,
                            work.title,
                            candidate,
                            "pending_review",
                            {"selectionStatus": status},
                        ))
                    _enqueue_review(manga_repository, work, ranked)
                    pending += 1
                else:
                    flow_repository.append_id_candidate(IdCandidateRecord(
                        execution_id=execution.execution_id,
                        work_id=work.work_id,
                        searched_title=work.title,
                        status="not_found",
                        details={"selectionStatus": status},
                    ))
                    pending += 1
                    not_found += 1
                flow_repository.append_log(
                    _log(
                        execution.execution_id,
                        "mangaupdates_search_finish",
                        "completed",
                        f"Consulta MangaUpdates finalizada para {work.title}.",
                        {
                            "workId": work.work_id,
                            "title": work.title,
                            "status": status,
                            "candidates": len(ranked),
                        },
                    )
                )
            except Exception as error:
                errors += 1
                pending += 1
                flow_repository.append_id_candidate(IdCandidateRecord(
                    execution_id=execution.execution_id,
                    work_id=work.work_id,
                    searched_title=work.title,
                    status="error",
                    details={"error": str(error)},
                ))
                flow_repository.append_log(
                    _log(
                        execution.execution_id,
                        "mangaupdates_search_error",
                        "error",
                        f"Consulta MangaUpdates falhou para {work.title}.",
                        {"workId": work.work_id, "title": work.title, "error": str(error)},
                        error_code="MANGAUPDATES_SEARCH_FAILED",
                    )
                )
            finally:
                flow_repository.update_stage_progress(
                    execution.execution_id,
                    StageId.RESOLVE_IDS,
                    Progress(
                        current=matched + pending,
                        total=len(eligible),
                    ),
                    current_item=work.title,
                )

        return SeriesSearchResult(
            searched=len(eligible),
            matched=matched,
            pending=pending,
            not_found=not_found,
            metrics={
                "catalogWorks": len(works),
                "alreadyResolved": already_resolved,
                "errors": errors,
            },
        )

    def get_metadata(self, selected_ids=None) -> MetadataUpdateResult:
        from manhwateca.mangaupdates_service import compatibility

        try:
            details = compatibility.fetch_confirmed_details_result(
                "reports/integrations/buscaIds.json",
                delay=0,
                limit=None,
                force_refresh=False,
                selected_ids=selected_ids,
            )
            return MetadataUpdateResult(
                updated=details.updated,
                skipped=details.skipped,
                failed=details.failed,
                metrics=details.metrics(),
            )
        except Exception:
            return MetadataUpdateResult()


def _candidate_record(
    execution_id: str,
    work_id: int,
    searched_title: str,
    candidate: dict,
    status: str,
    details: dict,
) -> IdCandidateRecord:
    return IdCandidateRecord(
        execution_id=execution_id,
        work_id=work_id,
        searched_title=searched_title,
        candidate_external_id=str(candidate.get("id")),
        candidate_title=candidate.get("titulo"),
        confidence=candidate.get("pontuacao"),
        status=status,
        details={**details, "candidate": candidate},
    )


def _enqueue_review(manga_repository, work, candidates) -> None:
    try:
        manga_repository.enqueue_decision(
            decision_type="mangaupdates_match",
            source="mangaupdates",
            title=work.title,
            manga_name=work.title,
            source_key=work.title,
            payload={
                "nome": work.title,
                "termo_busca": work.title,
                "candidatos": candidates,
            },
        )
        _commit_repository(manga_repository)
    except Exception:
        # A fila de decisão é compatibilidade operacional; o registro oficial
        # da execução continua em flow_id_candidates.
        return


def _commit_repository(repository) -> None:
    if hasattr(repository, "_connection"):
        repository._connection().commit()


def _search_with_deadline(search_function, title: str, timeout: int, kwargs: dict):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(search_function, title, **kwargs)
    try:
        return future.result(timeout=timeout + 1)
    except TimeoutError as error:
        future.cancel()
        raise TimeoutError(
            f"Consulta MangaUpdates excedeu {timeout}s para {title}."
        ) from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _log(
    execution_id: str,
    operation: str,
    status: str,
    message: str,
    details: dict,
    *,
    error_code: str | None = None,
):
    from manhwateca.flows.repository import FlowLogRecord

    return FlowLogRecord(
        execution_id=execution_id,
        stage=StageId.RESOLVE_IDS,
        operation=operation,
        status=status,
        error_code=error_code,
        message=message,
        details=details,
    )
