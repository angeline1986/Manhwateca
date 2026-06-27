from manhwateca.database.manga_repository import MangaRepository
from manhwateca.flows.domain import StageId
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
    ):
        self.flow_repository_factory = flow_repository_factory
        self.manga_repository_factory = manga_repository_factory
        self.search_function = search_function

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
        candidates = []
        matched = 0
        pending = 0
        not_found = 0

        for work in eligible:
            response = self.search_function(work.title, per_page=5)
            ranked = filter_relevant_candidates(
                rank_search_results(work.title, response)
            )
            selected, status = select_ranked_candidate(ranked)
            if selected:
                manga_repository.confirm_mangaupdates_id(
                    work.title,
                    selected["id"],
                    selected.get("titulo"),
                )
                candidates.append(_candidate_record(
                    execution.execution_id,
                    work.work_id,
                    work.title,
                    selected,
                    "auto_matched",
                    {"selectionStatus": status},
                ))
                matched += 1
            elif ranked:
                candidates.extend(
                    _candidate_record(
                        execution.execution_id,
                        work.work_id,
                        work.title,
                        candidate,
                        "pending_review",
                        {"selectionStatus": status},
                    )
                    for candidate in ranked
                )
                _enqueue_review(manga_repository, work, ranked)
                pending += 1
            else:
                candidates.append(IdCandidateRecord(
                    execution_id=execution.execution_id,
                    work_id=work.work_id,
                    searched_title=work.title,
                    status="not_found",
                    details={"selectionStatus": status},
                ))
                pending += 1
                not_found += 1

        flow_repository.replace_id_candidates(execution.execution_id, candidates)
        return SeriesSearchResult(
            searched=len(eligible),
            matched=matched,
            pending=pending,
            not_found=not_found,
            metrics={
                "catalogWorks": len(works),
                "alreadyResolved": already_resolved,
                "candidateRows": len(candidates),
            },
        )

    def get_metadata(self) -> MetadataUpdateResult:
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
    except Exception:
        # A fila de decisão é compatibilidade operacional; o registro oficial
        # da execução continua em flow_id_candidates.
        return
