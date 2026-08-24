from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_tracking_menu_route_and_page_exist():
    html = read("web/index.html")
    meta = read("web/js/state/appState.js")
    app = read("web/js/app.js")

    assert 'data-page="tracking"' in html
    assert "<span>Acompanhamento</span>" in html
    assert 'id="page-tracking"' in html
    assert "tracking:" in meta
    assert "initTrackingPage" in app
    assert "loadTracking()" in app


def test_tracking_uses_global_header_only():
    html = read("web/index.html")
    meta = read("web/js/state/appState.js")

    assert html.count('id="page-tracking"') == 1
    assert 'class="tracking-hero"' not in html
    assert 'id="trackingLastCheck"' not in html
    assert 'id="trackingMonitoredCount"' not in html
    assert meta.count("Acompanhar obras") == 1
    assert "Última catalogação" not in meta


def test_tracking_topbar_shows_release_check_metadata():
    app = read("web/js/app.js")
    router = read("web/js/router.js")
    page = read("web/js/pages/trackingPage.js")
    css = read("web/css/pages/releases.css")

    assert "topbarMeta: flowsCurrentMeta" in app
    assert 'topbar.classList.toggle("tracking", page === "tracking")' in router
    assert 'topbar.classList.remove("organization")' in router
    assert "tracking-topbar-meta" in page
    assert "Última verificação" in page
    assert "Última catalogação" not in page
    assert ".topbar.tracking .topbar-flow-meta" in css


def test_tracking_count_and_last_check_come_from_subscriptions():
    page = read("web/js/pages/trackingPage.js")

    assert "getReleasesSummary" not in page
    assert "subscriptions = Array.isArray(payload.items)" in page
    assert "payload.subscriptions" not in page
    assert "subscriptions.filter(isMonitored)" in page
    assert "item.last_checked_at" in page
    assert "latestCheckedAt(monitored)" in page
    assert "last_monitor_run" not in page


def test_tracking_work_filters_use_monitored_subscription_collection():
    page = read("web/js/pages/trackingPage.js")

    filtered = page.split("function filteredWorks", 1)[1].split(
        "function favoriteMangaIds", 1
    )[0]
    assert "subscriptions.filter(isMonitored).filter" in filtered
    assert 'filter === "favorites" && !item.favorite' in filtered
    assert 'filter === "not-favorites" && item.favorite' in filtered
    assert "String(item.title || \"\").toLocaleLowerCase" in filtered
    assert "releases.filter" not in filtered


def test_tracking_monitoring_contract_is_browser_compatible():
    page = read("web/js/pages/trackingPage.js")

    assert "Object.hasOwn(" not in page
    assert "Object.prototype.hasOwnProperty.call(item, field)" in page
    assert 'hasField(item, "monitored")' in page
    assert 'hasField(item, "enabled")' in page


def test_tracking_check_all_waits_and_reloads_subscriptions():
    page = read("web/js/pages/trackingPage.js")

    check_all = page.split("async function checkAll", 1)[1].split(
        "async function checkWork", 1
    )[0]
    assert "checkReleases()" in check_all
    assert "await waitForTask(payload?.id)" in check_all
    assert "await loadTracking()" in check_all
    wait = page.split("async function waitForTask", 1)[1].split(
        "function latestReleaseLabel", 1
    )[0]
    assert '["queued", "running"].includes(task.status)' in wait


def test_tracking_releases_use_days_and_filters():
    page = read("web/js/pages/trackingPage.js")
    html = read("web/index.html")

    assert "DAY_OPTIONS = [1, 7, 15, 30, 45, 60]" in page
    assert "getReleases({" in page
    assert "days," in page
    assert 'id="trackingFavoritesOnly"' in html
    assert 'id="trackingUnseenOnly"' in html
    assert 'id="trackingReleaseSearch"' in html
    assert 'id="trackingWindowDates"' not in html
    assert "A tabela acompanha a janela" not in html
    assert "windowDates" not in page


def test_tracking_releases_layout_keeps_controls_and_fields():
    page = read("web/js/pages/trackingPage.js")
    css = read("web/css/pages/releases.css")

    assert ".tracking-releases-panel .release-filters" in css
    assert ".tracking-releases-panel .tracking-window" in css
    assert "margin-bottom: 14px" in css
    assert "margin-bottom: -6px" in css
    assert "grid-template-columns: minmax(240px, 1fr) auto auto" in css
    assert ".tracking-releases-panel .release-table th:nth-child(4)" in css
    assert "${escapeHtml(item.title || \"\")}" in page
    assert "${escapeHtml(item.chapter || \"\")}" in page
    assert "${escapeHtml(dateOnly(item.release_date))}" in page
    assert "${escapeHtml(item.release_group || \"-\")}" in page
    assert "${escapeHtml(item.status)}" in page


def test_tracking_favorites_are_star_only_and_do_not_check_releases():
    page = read("web/js/pages/trackingPage.js")
    html = read("web/index.html")

    assert "updateReleaseFavorite" in page
    assert 'data-tracking-favorite="' in page
    assert "★" in page
    assert "☆" in page
    assert "Adicionar aos favoritos" not in html + page
    assert "Remover dos favoritos" not in html + page

    favorite_block = page.split("async function toggleFavorite", 1)[1].split(
        "async function checkAll", 1
    )[0]
    assert "checkReleases" not in favorite_block
    assert "checkReleaseWork" not in favorite_block


def test_tracking_general_and_individual_checks_are_distinct():
    page = read("web/js/pages/trackingPage.js")

    check_all = page.split("async function checkAll", 1)[1].split(
        "async function checkWork", 1
    )[0]
    check_work = page.split("async function checkWork", 1)[1].split(
        "function filteredWorks", 1
    )[0]

    assert "checkReleases()" in check_all
    assert "checkReleaseWork(mangaId)" in check_work


def test_dashboard_release_section_still_exists():
    html = read("web/index.html")
    overview = read("web/js/pages/overviewPage.js")

    assert 'id="page-overview"' in html
    assert 'id="releaseList"' in html
    assert "loadReleaseDashboard" in overview
