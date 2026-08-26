from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_tracking_task_wait_no_longer_stops_after_30_seconds():
    page = read("web/js/pages/trackingPage.js")
    wait = page.split("async function waitForTask", 1)[1].split(
        "function latestReleaseLabel", 1
    )[0]
    assert "const maxAttempts = 600" in wait
    assert "index < maxAttempts" in wait
    assert "throw new Error" in wait
    assert "index < 30" not in wait


def test_tracking_history_is_compact_and_expandable():
    page = read("web/js/pages/trackingPage.js")
    assert "let historyExpanded = false" in page
    assert "rows.slice(0, 5)" in page
    assert 'data-tracking-history-toggle' in page
    assert '"Ver menos"' in page
    assert "`Ver mais (${hiddenCount})`" in page


def test_tracking_work_queue_does_not_stretch_with_long_history():
    css = read("web/css/pages/releases.css")
    assert "/* tracking follow-up: compact queue + collapsible history */" in css
    block = css.split("/* tracking follow-up: compact queue + collapsible history */", 1)[1]
    assert ".tracking-work-list" in block
    assert "align-content: start" in block
