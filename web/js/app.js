import { initSidebar } from "./layout/sidebar.js";
import { initActionsPage } from "./pages/actionsPage.js";
import { initEditorialPage } from "./pages/editorialPage.js";
import { initFlowsPage } from "./pages/flowsPage.js";
import { initLibraryPage } from "./pages/libraryPage.js";
import { initMangaUpdatesPage } from "./pages/mangaupdatesPage.js";
import { initNotionPage } from "./pages/notionPage.js";
import { initOrganizationPage } from "./pages/organizationPage.js";
import { initOverviewPage } from "./pages/overviewPage.js";
import { initTrackingPage } from "./pages/trackingPage.js";
import { initRouter } from "./router.js";
import { initPendingActions, pendingRequiresConfirmation } from "./tasks/pendingActions.js";
import { initTaskRunner } from "./tasks/taskRunner.js";

const byId = id => document.getElementById(id);
const grid = byId("statusGrid"), refreshButton = byId("refresh");
const pendingList = byId("pendingList"), organizationPendingList = byId("organizationPendingList");
const organizationCatalogPendingList = byId("organizationCatalogPendingList");
const catalogPendingCount = byId("catalogPendingCount"), catalogPendingMeta = byId("catalogPendingMeta");
const catalogAllPending = byId("catalogAllPending"), refreshCatalogPending = byId("refreshCatalogPending");
const diagnosticGrid = byId("diagnosticGrid"), refreshDiagnostics = byId("refreshDiagnostics");
const releaseCards = byId("releaseCards"), releaseList = byId("releaseList");
const releaseFeedback = byId("releaseFeedback"), releaseCheckNow = byId("releaseCheckNow");
const releaseMonitorStatus = byId("releaseMonitorStatus");
const releaseSearch = byId("releaseSearch"), releaseUnseenOnly = byId("releaseUnseenOnly");
const trackingCheckAll = byId("trackingCheckAll"), trackingDaysSlider = byId("trackingDaysSlider");
const trackingWindowLabel = byId("trackingWindowLabel"), trackingReleaseCount = byId("trackingReleaseCount");
const trackingReleaseSearch = byId("trackingReleaseSearch");
const trackingFavoritesOnly = byId("trackingFavoritesOnly"), trackingUnseenOnly = byId("trackingUnseenOnly");
const trackingFeedback = byId("trackingFeedback"), trackingReleaseList = byId("trackingReleaseList");
const trackingReleasePagination = byId("trackingReleasePagination");
const trackingReleasePrev = byId("trackingReleasePrev"), trackingReleaseNext = byId("trackingReleaseNext");
const trackingReleasePageCurrent = byId("trackingReleasePageCurrent"), trackingReleasePageTotal = byId("trackingReleasePageTotal");
const trackingReleasePageRange = byId("trackingReleasePageRange");
const trackingWorksCount = byId("trackingWorksCount"), trackingFavoriteCount = byId("trackingFavoriteCount");
const trackingUpdatedCount = byId("trackingUpdatedCount"), trackingWorkSearch = byId("trackingWorkSearch");
const trackingWorkFilter = byId("trackingWorkFilter"), trackingWorkList = byId("trackingWorkList");
const trackingWorkDetail = byId("trackingWorkDetail");
const actionGrid = byId("actionGrid"), mangaActionGrid = byId("mangaActionGrid");
const notionActionGrid = byId("notionActionGrid"), supportActionGrid = byId("supportActionGrid");
const taskList = byId("taskList"), taskToast = byId("taskToast"), viewTaskProgress = byId("viewTaskProgress");
const taskProgress = byId("taskProgress"), taskResultLink = byId("taskResultLink");
const reviewForm = byId("reviewForm"), reviewNote = byId("reviewNote"), reviewFeedback = byId("reviewFeedback");
const catalogSummary = byId("catalogSummary"), catalogSource = byId("catalogSource");
const catalogChanges = byId("catalogChanges"), catalogList = byId("catalogList"), catalogSearch = byId("catalogSearch");
const reviewSummary = byId("reviewSummary"), idReviewList = byId("idReviewList"), reviewSearch = byId("reviewSearch");
const applyDecisionsButton = byId("applyDecisions"), decisionFeedback = byId("decisionFeedback");
const organizationReviewSummary = byId("organizationReviewSummary"), organizationIdReviewList = byId("organizationIdReviewList");
const organizationReviewSearch = byId("organizationReviewSearch"), organizationApplyDecisionsButton = byId("organizationApplyDecisions");
const organizationDecisionFeedback = byId("organizationDecisionFeedback");
const mangaCacheSummary = byId("mangaCacheSummary"), mangaCacheLists = byId("mangaCacheLists");
const refreshMangaUpdatesStatus = byId("refreshMangaUpdatesStatus"), apiSearchForm = byId("apiSearchForm");
const apiSearchQuery = byId("apiSearchQuery"), apiSearchFeedback = byId("apiSearchFeedback"), apiSearchResults = byId("apiSearchResults");
const notionSummary = byId("notionSummary"), notionMeta = byId("notionMeta"), notionLists = byId("notionLists");
const notionSyncStatus = byId("notionSyncStatus"), notionCatalogPanel = byId("notionCatalogPanel"), refreshNotion = byId("refreshNotion");
const metadataSummary = byId("metadataSummary"), metadataMeta = byId("metadataMeta"), metadataUpdates = byId("metadataUpdates");
const metadataAlerts = byId("metadataAlerts"), refreshMetadata = byId("refreshMetadata");
const editorialSummary = byId("editorialSummary"), editorialFilters = byId("editorialFilters");
const editorialList = byId("editorialList"), editorialSearch = byId("editorialSearch"), editorialFeedback = byId("editorialFeedback");
const workflowSteps = byId("workflowSteps"), workflowNotice = byId("workflowNotice"), workflowFeedback = byId("workflowFeedback");
const startWorkflow = byId("startWorkflow"), resumeWorkflow = byId("resumeWorkflow");
const flowsStartWorkflow = byId("flowsStartWorkflow"), flowsResumeWorkflow = byId("flowsResumeWorkflow");
const flowsSummary = byId("flowsSummary"), flowsProgress = byId("flowsProgress"), flowsStageList = byId("flowsStageList");
const flowsCurrentTitle = byId("flowsCurrentTitle"), flowsCurrentDescription = byId("flowsCurrentDescription");
const flowsCurrentMeta = byId("flowsCurrentMeta"), flowsCurrentCards = byId("flowsCurrentCards");
const flowsFeedback = byId("flowsFeedback");
const confirmationDialog = byId("confirmationDialog"), confirmationTitle = byId("confirmationTitle");
const confirmationText = byId("confirmationText");
const sidebarLayout = initSidebar();
const router = initRouter({ onPageChange: sidebarLayout.closeSidebar });
const showPage = router.showPage;

const overviewPage = initOverviewPage({
  grid,
  refreshButton,
  pendingList,
  organizationPendingList,
  diagnosticGrid,
  refreshDiagnostics,
  releaseCards,
  releaseList,
  releaseFeedback,
  releaseCheckNow,
  releaseMonitorStatus,
  releaseSearch,
  releaseUnseenOnly,
});
const loadStatus = overviewPage.loadStatus;
const loadDiagnostics = overviewPage.loadDiagnostics;
const loadPendingActions = overviewPage.loadPendingActions;
const trackingPage = initTrackingPage({
  topbarMeta: flowsCurrentMeta,
  checkAll: trackingCheckAll,
  daysSlider: trackingDaysSlider,
  windowLabel: trackingWindowLabel,
  releaseCount: trackingReleaseCount,
  releaseSearch: trackingReleaseSearch,
  favoritesOnly: trackingFavoritesOnly,
  unseenOnly: trackingUnseenOnly,
  feedback: trackingFeedback,
  releaseList: trackingReleaseList,
  pagination: trackingReleasePagination,
  pagePrev: trackingReleasePrev,
  pageNext: trackingReleaseNext,
  pageCurrent: trackingReleasePageCurrent,
  pageTotal: trackingReleasePageTotal,
  pageRange: trackingReleasePageRange,
  worksCount: trackingWorksCount,
  favoriteCount: trackingFavoriteCount,
  updatedCount: trackingUpdatedCount,
  workSearch: trackingWorkSearch,
  workFilter: trackingWorkFilter,
  workList: trackingWorkList,
  detail: trackingWorkDetail,
});
const loadTracking = trackingPage.loadTracking;
const libraryPage = initLibraryPage({
  elements: {
    catalogSummary,
    catalogSource,
    catalogChanges,
    catalogList,
    catalogSearch,
  },
  onAction: event => actionsPage.handleActionClick(event),
});
const loadCatalog = libraryPage.loadCatalog;
const mangaUpdatesPage = initMangaUpdatesPage({
  elements: {
    reviewSummary,
    idReviewList,
    reviewSearch,
    applyDecisionsButton,
    decisionFeedback,
    organizationReviewSummary,
    organizationIdReviewList,
    organizationReviewSearch,
    organizationApplyDecisionsButton,
    organizationDecisionFeedback,
    mangaCacheSummary,
    mangaCacheLists,
    refreshMangaUpdatesStatus,
    apiSearchForm,
    apiSearchQuery,
    apiSearchFeedback,
    apiSearchResults,
  },
  onDecisionsApplied: loadPendingActions,
});
const loadIdReview = mangaUpdatesPage.loadIdReview;
const loadMangaUpdatesStatus = mangaUpdatesPage.loadMangaUpdatesStatus;
const organizationPage = initOrganizationPage({
  elements: {
    organizationCatalogPendingList,
    catalogPendingCount,
    catalogPendingMeta,
    catalogAllPending,
    refreshCatalogPending,
  },
  getNotionUncataloged: () => notionPage.getNotionUncataloged(),
  loadCatalog,
  loadNotionStatus: () => loadNotionStatus(),
  loadPendingActions,
  startTask: (...args) => startTask(...args),
});
const notionPage = initNotionPage({
  elements: {
    notionSummary,
    notionMeta,
    notionLists,
    notionSyncStatus,
    notionCatalogPanel,
    refreshNotion,
    metadataSummary,
    metadataMeta,
    metadataUpdates,
    metadataAlerts,
    refreshMetadata,
    notionActionGrid,
    actionGrid,
  },
  showPage,
  onCatalogPendingData: organizationPage.renderCatalogPending,
});
const loadNotionStatus = notionPage.loadNotionStatus;
const loadMetadataStatus = notionPage.loadMetadataStatus;

const taskRunner = initTaskRunner({
  elements: {
    taskList,
    taskToast,
    viewTaskProgress,
    taskProgress,
    taskResultLink,
    confirmationDialog,
    confirmationTitle,
    confirmationText,
  },
  callbacks: {
    loadCatalog,
    loadStatus,
    loadNotionStatus,
    loadPendingActions,
    loadIdReview,
    loadMangaUpdatesStatus,
    loadMetadataStatus,
  },
  showPage,
  getNotionUncataloged: notionPage.getNotionUncataloged,
});
const startTask = taskRunner.startTask;
const loadTasks = taskRunner.loadTasks;
const goToNextStep = taskRunner.goToNextStep;
const actionsPage = initActionsPage({
  elements: {
    actionGrid,
    mangaActionGrid,
    notionActionGrid,
    supportActionGrid,
    quickGuide: document.querySelector(".quick-guide"),
  },
  startTask,
});
const loadActions = actionsPage.loadActions;
const editorialPage = initEditorialPage({
  elements: {
    reviewForm,
    reviewNote,
    reviewFeedback,
    editorialSummary,
    editorialFilters,
    editorialList,
    editorialSearch,
    editorialFeedback,
  },
  onSaved: loadCatalog,
});
const loadEditorial = editorialPage.loadEditorial;

const flowsPage = initFlowsPage({
  workflowSteps,
  workflowNotice,
  workflowFeedback,
  startWorkflow,
  resumeWorkflow,
  flowsStartWorkflow,
  flowsResumeWorkflow,
  flowsSummary,
  flowsProgress,
  flowsStageList,
  flowsCurrentTitle,
  flowsCurrentDescription,
  flowsCurrentMeta,
  flowsCurrentCards,
  flowsFeedback,
}, { showPage });
const loadWorkflow = flowsPage.loadWorkflow;

initPendingActions({
  lists: [pendingList, organizationPendingList],
  organizationPendingList,
  startTask,
  goToNextStep,
});

Promise.all([
  loadStatus(), loadDiagnostics(), loadActions(), loadCatalog(),
  loadIdReview(), loadMangaUpdatesStatus(), loadTasks()
  , loadNotionStatus(), loadMetadataStatus(), loadEditorial(), loadWorkflow(),
  loadTracking()
]);
