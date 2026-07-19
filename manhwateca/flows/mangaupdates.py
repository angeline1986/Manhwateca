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
from manhwateca.mangaupdates_service.client import get_series
from manhwateca.mangaupdates_service.details import summarize_series
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
        detail_function=get_series,
        summarize_function=summarize_series,
        per_page: int = 5,
        timeout: int = 8,
        retries: int = 0,
    ):
        self.flow_repository_factory = flow_repository_factory
        self.manga_repository_factory = manga_repository_factory
        self.search_function = search_function
        self.detail_function = detail_function
        self.summarize_function = summarize_function
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
                    confirmation = manga_repository.confirm_mangaupdates_id_by_work_id(
                        work.work_id,
                        selected["id"],
                        found_title=selected.get("titulo"),
                    )
                    _commit_repository(manga_repository)
                    if confirmation:
                        flow_repository.append_id_candidate(_candidate_record(
                            execution.execution_id,
                            work.work_id,
                            work.title,
                            selected,
                            "auto_matched",
                            {"selectionStatus": status},
                        ))
                        matched += 1
                    elif confirmation.status == "external_id_already_assigned":
                        flow_repository.append_id_candidate(_candidate_record(
                            execution.execution_id,
                            work.work_id,
                            work.title,
                            selected,
                            "pending_review",
                            {
                                "selectionStatus": status,
                                **_confirmation_details(confirmation),
                            },
                        ))
                        _enqueue_review(manga_repository, work, [selected])
                        pending += 1
                    else:
                        flow_repository.append_id_candidate(_candidate_record(
                            execution.execution_id,
                            work.work_id,
                            work.title,
                            selected,
                            "error",
                            {
                                "selectionStatus": status,
                                **_confirmation_details(confirmation),
                            },
                        ))
                        pending += 1
                        errors += 1
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
        repository = self.manga_repository_factory()
        return _fetch_metadata_from_repository(
            repository,
            selected_ids=selected_ids,
            detail_function=self.detail_function,
            summarize_function=self.summarize_function,
        )


def _fetch_metadata_from_repository(
    repository,
    *,
    selected_ids,
    detail_function,
    summarize_function,
) -> MetadataUpdateResult:
    selected_work_ids = _ordered_ids(_normalize_work_ids(selected_ids))
    if not selected_work_ids:
        return MetadataUpdateResult(metrics=_metadata_metrics(
            selected_work_ids=(),
            attempted_work_ids=(),
            processed_work_ids=(),
            failed_work_ids=(),
            skipped_work_ids=(),
        ))

    records = repository.list_mangas_by_ids(selected_work_ids)
    by_id = {
        int(getattr(record, "id", 0) or 0): record
        for record in records
        if getattr(record, "id", None) is not None
    }
    updated = 0
    failed_ids = []
    skipped_ids = []
    attempted_ids = []
    processed_ids = []

    for work_id in selected_work_ids:
        manga = by_id.get(work_id)
        if manga is None or not str(getattr(manga, "work_code", "") or "").strip():
            skipped_ids.append(work_id)
            continue
        processed_ids.append(work_id)
        if not _metadata_needs_update(manga):
            continue
        attempted_ids.append(work_id)
        try:
            raw_data = detail_function(manga.work_code)
            if not raw_data:
                failed_ids.append(work_id)
                continue
            summary = summarize_function(raw_data)
            if repository.update_mangaupdates_fields(
                manga.title,
                manga.work_code,
                summary,
            ):
                updated += 1
            else:
                failed_ids.append(work_id)
        except Exception:
            failed_ids.append(work_id)

    failed_set = set(failed_ids)
    processed_ids = [work_id for work_id in processed_ids if work_id not in failed_set]
    return MetadataUpdateResult(
        updated=updated,
        skipped=len(skipped_ids) + max(0, len(attempted_ids) - updated - len(failed_ids)),
        failed=len(failed_ids),
        metrics=_metadata_metrics(
            selected_work_ids=selected_work_ids,
            attempted_work_ids=attempted_ids,
            processed_work_ids=processed_ids,
            failed_work_ids=failed_ids,
            skipped_work_ids=skipped_ids,
        ),
    )


def _metadata_needs_update(manga) -> bool:
    return (
        not str(getattr(manga, "mangaupdates_url", "") or "").strip()
        or not str(getattr(manga, "cover_url", "") or "").strip()
    )


def _metadata_metrics(
    *,
    selected_work_ids,
    attempted_work_ids,
    processed_work_ids,
    failed_work_ids,
    skipped_work_ids,
) -> dict:
    return {
        "selected_work_ids": list(selected_work_ids),
        "attempted_work_ids": list(_ordered_ids(attempted_work_ids)),
        "processed_work_ids": list(_ordered_ids(processed_work_ids)),
        "failed_work_ids": list(_ordered_ids(failed_work_ids)),
        "skipped_work_ids": list(_ordered_ids(skipped_work_ids)),
    }


def _normalize_work_ids(values) -> list[int]:
    if values is None:
        return []
    result = []
    for value in values:
        try:
            work_id = int(value)
        except (TypeError, ValueError):
            continue
        if work_id > 0 and work_id not in result:
            result.append(work_id)
    return result


def _ordered_ids(values) -> tuple[int, ...]:
    ordered = []
    for value in values or ():
        try:
            work_id = int(value)
        except (TypeError, ValueError):
            continue
        if work_id > 0 and work_id not in ordered:
            ordered.append(work_id)
    return tuple(ordered)


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


def _confirmation_details(result) -> dict:
    return {
        "reason": result.status,
        "candidateExternalId": result.series_id,
        "targetWorkId": result.work_id,
        "existingWorkId": result.existing_work_id,
        "existingTitle": result.existing_title,
        "message": result.message,
    }


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
