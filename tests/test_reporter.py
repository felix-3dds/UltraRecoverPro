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
