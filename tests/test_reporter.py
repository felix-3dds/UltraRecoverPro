from pathlib import Path

from post_processing.reporter import ForensicReporter


def test_generate_html_escapes_untrusted_fields(tmp_path: Path) -> None:
    reporter = ForensicReporter(case_id='CASE-<script>alert(1)</script>', investigator='Inv <script>')
    reporter.add_entry(
        filename='evidence-<script>alert(1)</script>.jpg',
        ftype='JPEG<script>',
        size=4096,
        offset=16,
        hash_sha256='hash-<script>',
    )

    report_path = tmp_path / 'report.html'
    reporter.generate_html(str(report_path))

    content = report_path.read_text(encoding='utf-8')
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content
    assert 'CASE-&lt;script&gt;alert(1)&lt;/script&gt;' in content
    assert 'JPEG&lt;script&gt;' in content
    assert 'hash-&lt;script&gt;' in content


def test_export_json_includes_integrity_summary(tmp_path: Path) -> None:
    reporter = ForensicReporter(case_id='CASE-1', investigator='Analyst')
    reporter.add_entry('f1.jpg', 'JPEG', 1000, 100, 'dup-hash')
    reporter.add_entry('f2.jpg', 'JPEG', 2000, 200, 'dup-hash')

    json_path = tmp_path / 'report.json'
    reporter.export_json(str(json_path))

    payload = __import__('json').loads(json_path.read_text(encoding='utf-8'))
    assert payload['integrity']['hashes_total'] == 2
    assert payload['integrity']['hashes_unicos'] == 1
    assert payload['integrity']['hashes_duplicados'] == 1


def test_export_csv_generates_tabular_report(tmp_path: Path) -> None:
    reporter = ForensicReporter(case_id='CASE-2', investigator='Analyst')
    reporter.add_entry('evidence.jpg', 'JPEG', 4096, 16, 'a' * 64)

    csv_path = tmp_path / 'report.csv'
    reporter.export_csv(str(csv_path))

    content = csv_path.read_text(encoding='utf-8')
    assert 'name,type,size_bytes,size_kb,offset,hash' in content
    assert 'evidence.jpg,JPEG,4096,4.0,0x10,' in content
