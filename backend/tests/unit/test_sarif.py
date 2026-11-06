from patchpilot.constants import Severity
from patchpilot.scanning.sarif import parse_sarif_content


def test_parse_sample_sarif():
    sample_sarif = {
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "semgrep",
                        "rules": [
                            {
                                "id": "python.sqlalchemy.security.injection",
                                "properties": {"tags": ["CWE-89"]},
                            }
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "python.sqlalchemy.security.injection",
                        "level": "error",
                        "message": {"text": "Detected SQL Injection vulnerability"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/db.py"},
                                    "region": {
                                        "startLine": 42,
                                        "endLine": 44,
                                        "snippet": {"text": "cursor.execute(f'SELECT...')"},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ]
    }

    findings = parse_sarif_content(sample_sarif)
    assert len(findings) == 1
    f = findings[0]
    assert f.scanner == "semgrep"
    assert f.rule_id == "python.sqlalchemy.security.injection"
    assert f.cwe == "CWE-89"
    assert f.severity == Severity.HIGH
    assert f.file_path == "app/db.py"
    assert f.start_line == 42
    assert len(f.fingerprint) == 64

