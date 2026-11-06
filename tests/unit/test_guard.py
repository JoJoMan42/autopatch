from patchpilot.repair.guard import PatchGuard


def test_guard_valid_patch():
    guard = PatchGuard()
    diff = """--- a/shop/db.py\n+++ b/shop/db.py\n@@ -40,2 +40,2 @@\n-query = f"SELECT * FROM users WHERE name = '{name}'"\n+query = "SELECT * FROM users WHERE name = %s"\n"""
    report = guard.verify_patch(
        diff_text=diff,
        expected_target_file="shop/db.py",
        cwe="CWE-89",
    )
    assert report.ok
    assert len(report.issues) == 0
    assert report.changed_files == ["shop/db.py"]


def test_guard_rejects_out_of_scope_file():
    guard = PatchGuard()
    diff = """--- a/unauthorized.py\n+++ b/unauthorized.py\n@@ -1,1 +1,1 @@\n-pass\n+pass\n"""
    report = guard.verify_patch(
        diff_text=diff,
        expected_target_file="shop/db.py",
    )
    assert not report.ok
    assert any(i.code == "OUT_OF_SCOPE_FILE" for i in report.issues)


def test_guard_rejects_suppression_comment():
    guard = PatchGuard()
    diff = """--- a/shop/db.py\n+++ b/shop/db.py\n@@ -40,1 +40,1 @@\n-cursor.execute(query)\n+cursor.execute(query)  # nosec B608\n"""
    report = guard.verify_patch(
        diff_text=diff,
        expected_target_file="shop/db.py",
    )
    assert not report.ok
    assert any(i.code == "SUPPRESSION_COMMENT_BANNED" for i in report.issues)


def test_guard_rejects_banned_ast_calls():
    guard = PatchGuard()
    diff = """--- a/shop/db.py\n+++ b/shop/db.py\n@@ -10,1 +10,1 @@\n-pass\n+eval('print(1)')\n"""
    patched_code = "eval('print(1)')\n"
    report = guard.verify_patch(
        diff_text=diff,
        expected_target_file="shop/db.py",
        patched_file_content=patched_code,
    )
    assert not report.ok
    assert any(i.code == "BANNED_CALL" for i in report.issues)

