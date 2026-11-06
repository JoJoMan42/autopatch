from __future__ import annotations

import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field


class TestSummary(BaseModel):
    tests: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    failed_test_names: list[str] = Field(default_factory=list)


def parse_junit_xml(xml_content: str) -> TestSummary:
    """Parse JUnit XML format test report."""
    if not xml_content or not xml_content.strip():
        return TestSummary()

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return TestSummary()

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    failed_names: list[str] = []

    # Handle testsuites or single testsuite root
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    if not suites and root.tag == "testsuites":
        suites = list(root)

    for suite in suites:
        total_tests += int(suite.attrib.get("tests", 0))
        total_failures += int(suite.attrib.get("failures", 0))
        total_errors += int(suite.attrib.get("errors", 0))
        total_skipped += int(suite.attrib.get("skipped", 0))

        for tc in suite.findall("testcase"):
            tc_name = f"{tc.attrib.get('classname', '')}.{tc.attrib.get('name', '')}"
            if tc.find("failure") is not None or tc.find("error") is not None:
                failed_names.append(tc_name)

    return TestSummary(
        tests=total_tests,
        failures=total_failures,
        errors=total_errors,
        skipped=total_skipped,
        failed_test_names=failed_names,
    )

