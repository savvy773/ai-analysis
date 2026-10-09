"""재실행 제한, 실패 창 유지, 리포트 저장 오류의 회귀 검사."""
import builtins
import contextlib
import io
import runpy
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ai_analysis import cli, data, web

launcher = SimpleNamespace(**runpy.run_path(str(Path(__file__).resolve().parents[1] / "ai_compare.py")))
original_import = builtins.__import__


def import_failure(error):
    def import_module(name, *args, **kwargs):
        if name == "ai_analysis.cli":
            raise error
        return original_import(name, *args, **kwargs)
    return import_module


class LauncherTest(unittest.TestCase):
    def test_internal_import_error_is_reported_without_restarting(self):
        stderr = io.StringIO()
        with (patch("builtins.__import__", side_effect=import_failure(ImportError("broken symbol"))),
              patch("subprocess.call") as subprocess_call,
              contextlib.redirect_stderr(stderr)):
            self.assertEqual(launcher.execute(), 1)
        subprocess_call.assert_not_called()
        self.assertIn("broken symbol", stderr.getvalue())

    def test_missing_dependency_restarts_once_and_child_does_not_pause(self):
        error = ModuleNotFoundError("missing rich", name="rich")
        with (patch("builtins.__import__", side_effect=import_failure(error)),
              patch("subprocess.call", return_value=1) as subprocess_call,
              patch.dict("os.environ", {}, clear=True)):
            self.assertEqual(launcher.execute(), 1)
            child_env = subprocess_call.call_args.kwargs["env"]
            self.assertEqual(child_env["AA_PAUSE"], "0")
            with patch.dict("os.environ", child_env, clear=True), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(launcher.execute(), 1)
        subprocess_call.assert_called_once()

    def test_double_click_failure_pauses_but_successful_report_does_not(self):
        namespace = launcher.run.__globals__
        for code, expected in [(1, True), (0, False)]:
            with (self.subTest(code=code),
                  patch.dict(namespace, opened_by_double_click=lambda: True, execute=lambda: code),
                  patch.dict("sys.__dict__", argv=["ai_compare.py"]),
                  patch("builtins.input", return_value="") as prompt):
                self.assertEqual(launcher.run(), code)
                self.assertEqual(prompt.called, expected)

    def test_argument_error_also_pauses(self):
        def invalid_args():
            raise SystemExit(2)
        with (patch.dict(launcher.run.__globals__, opened_by_double_click=lambda: True, execute=invalid_args),
              patch("builtins.input", return_value="") as prompt):
            self.assertEqual(launcher.run(), 2)
        prompt.assert_called_once()

    def test_pause_tolerates_closed_stdin(self):
        with patch("builtins.input", side_effect=EOFError):
            launcher.pause_if_double_clicked(True)


class ReportErrorsTest(unittest.TestCase):
    def test_write_error_returns_failure_without_opening_browser(self):
        args = SimpleNamespace(html=None, refresh=True, maker="all", sort="cost", top=20,
                               filter=None, min=40, min_terminal=0, out=None)
        stderr = io.StringIO()
        with (patch.object(data, "load", return_value=([], datetime.now(timezone.utc), None)),
              patch.object(web, "write", side_effect=PermissionError("output denied")),
              patch("webbrowser.open") as browser,
              contextlib.redirect_stderr(stderr)):
            self.assertEqual(cli.open_report(args), 1)
        browser.assert_not_called()
        self.assertIn(str(web.REPORT_PATH), stderr.getvalue())
        self.assertIn("output denied", stderr.getvalue())
