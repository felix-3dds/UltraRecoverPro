import json
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from post_processing.reporter import ForensicReporter


class _SimpleHTMLValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.seen_tags: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        self.seen_tags.add(tag)


def test_reporter_exports_required_json_structure(tmp_path: Path) -> None:
    reporter = ForensicReporter(case_id="case-001", investigator="tester")
    reporter.add_entry(
        filename="JPEG_0001",
        ftype="JPEG",
        size=1024,
        offset=1234,
        hash_sha256="a" * 64,
    )

    json_path = tmp_path / "report.json"
    reporter.export_json(str(json_path))

    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert {"case_id", "investigator", "start_time", "totals", "files"}.issubset(data.keys())
    assert {"files", "by_type"}.issubset(data["totals"].keys())
    assert data["totals"]["files"] == 1

    first = data["files"][0]
    required_fields = {"name", "type", "size_bytes", "size_kb", "offset", "hash"}
    assert required_fields.issubset(first.keys())


def test_reporter_generates_valid_html_document(tmp_path: Path) -> None:
    reporter = ForensicReporter(case_id="case-html", investigator="tester")
    reporter.add_entry(
        filename="PNG_0001",
        ftype="PNG",
        size=2048,
        offset=4096,
        hash_sha256="b" * 64,
    )

    html_path = tmp_path / "report.html"
    reporter.generate_html(str(html_path))

    content = html_path.read_text(encoding="utf-8")
    parser = _SimpleHTMLValidator()
    parser.feed(content)

    assert "<!DOCTYPE html>" in content
    assert {"html", "head", "body", "table", "script"}.issubset(parser.seen_tags)
    assert "Informe Forense de Recuperación" in content
