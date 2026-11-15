"""First-run launcher tests; no network or package installation is performed."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.launcher import bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.python = bootstrap.environment_python(self.root / ".venv")
        root_patch = patch.object(bootstrap, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def test_existing_qt_starts_without_install(self):
        with patch.object(bootstrap, "qt_ready", return_value=(True, "")), \
                patch.object(bootstrap, "launch_checked", return_value=0) as launch, \
                patch("builtins.input") as prompt, patch("subprocess.run") as run:
            self.assertEqual(bootstrap.main(), 0)
        launch.assert_called_once()
        prompt.assert_not_called()
        run.assert_not_called()

    def test_decline_setup(self):
        with patch.object(bootstrap, "qt_ready", return_value=(False, "missing")), \
                patch("builtins.input", return_value="n"), patch("subprocess.run") as run:
            self.assertEqual(bootstrap.main(), 0)
        run.assert_not_called()
        self.assertFalse(self.python.exists())

    def test_confirm_creates_environment_installs_and_launches(self):
        with patch.object(bootstrap, "qt_ready", return_value=(False, "missing")), \
                patch("builtins.input", return_value="j"), patch("subprocess.run") as run, \
                patch.object(bootstrap, "run_in_environment", return_value=0) as launch:
            self.assertEqual(bootstrap.main(), 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0],
                         [sys.executable, "-m", "venv", str(self.root / ".venv")])
        self.assertEqual(run.call_args_list[1].args[0],
                         [str(self.python), "-m", "pip", "install", "-r",
                          str(self.root / "requirements.txt")])
        launch.assert_called_once_with(self.python)

    def test_reuse_existing_environment(self):
        self.python.parent.mkdir(parents=True)
        self.python.touch()
        with patch.object(bootstrap, "qt_ready", return_value=(False, "missing")), \
                patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run, \
                patch.object(bootstrap, "run_in_environment", return_value=0) as launch, \
                patch("builtins.input") as prompt:
            self.assertEqual(bootstrap.main(), 0)
        run.assert_called_once()
        launch.assert_called_once_with(self.python)
        prompt.assert_not_called()

    def test_install_failure_does_not_launch(self):
        with patch.object(bootstrap, "qt_ready", return_value=(False, "missing")), \
                patch("builtins.input", return_value="yes"), \
                patch("subprocess.run", side_effect=[None, subprocess.CalledProcessError(1, "pip")]), \
                patch.object(bootstrap, "run_in_environment") as launch:
            self.assertEqual(bootstrap.main(), 1)
        launch.assert_not_called()

    def test_failed_qt_check_after_install_does_not_loop(self):
        with patch.object(bootstrap, "qt_ready", return_value=(False, "bad DLL")), \
                patch("builtins.input") as prompt:
            self.assertEqual(bootstrap.launch_checked(), 1)
        prompt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
