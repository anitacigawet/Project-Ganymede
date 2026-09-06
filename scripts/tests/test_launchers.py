"""Run exact launcher copies with inert native/service fixtures and real dotenv.

Run with the installed project Python: python -m unittest discover -s scripts/tests -v
No package installation, Claude invocation, application listener or private .env is used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
POWERSHELL = Path(os.environ.get("WINDIR", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
SHELL = shutil.which("sh") or ("C:/Program Files/Git/bin/sh.exe" if Path("C:/Program Files/Git/bin/sh.exe").is_file() else None)

NATIVE_SOURCE = r'''
using System;
using System.IO;
using System.Diagnostics;
public static class LauncherFixture {
    public static int Main(string[] args) {
        string command = String.Join(" ", args);
        File.AppendAllText(Environment.GetEnvironmentVariable("FIXTURE_LOG"), command + "\n");
        if (command == "-m app.cli_preflight") {
            var info = new ProcessStartInfo(Environment.GetEnvironmentVariable("FIXTURE_PYTHON"), command);
            info.UseShellExecute = false;
            var child = Process.Start(info);
            child.WaitForExit();
            return child.ExitCode;
        }
        string stage = command.Contains("venv") ? "venv" : command.Contains("--upgrade") ? "upgrade" : "requirements";
        if (Environment.GetEnvironmentVariable("FIXTURE_FAIL") == stage) return 47;
        if (stage == "venv") {
            string target = Path.Combine(args[args.Length - 1], "Scripts");
            Directory.CreateDirectory(target);
            File.Copy(System.Reflection.Assembly.GetExecutingAssembly().Location, Path.Combine(target, "python.exe"), true);
        }
        return 0;
    }
}
'''


class LauncherFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.native_temp = tempfile.TemporaryDirectory(prefix="ganymede-native-test-")
        cls.native = Path(cls.native_temp.name) / "python.exe"
        if os.name == "nt":
            source = Path(cls.native_temp.name) / "fixture.cs"
            source.write_text(NATIVE_SOURCE, encoding="utf-8")
            compile_script = Path(cls.native_temp.name) / "compile.ps1"
            compile_script.write_text(
                "param($Source, $Output)\n$ErrorActionPreference = 'Stop'\n"
                "Add-Type -Path $Source -OutputAssembly $Output -OutputType ConsoleApplication\n",
                encoding="utf-8",
            )
            subprocess.run([str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(compile_script), str(source), str(cls.native)], check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.native_temp.cleanup()

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="ganymede launcher test ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "fixture-bin"
        self.backend = self.root / "ganymede-backend"
        self.log = self.root / "commands.txt"
        for relative in ["scripts", "fixture-bin", "ganymede-ui/node_modules", "ganymede-backend/app/services"]:
            (self.root / relative).mkdir(parents=True)
        for relative in ["scripts/setup.ps1", "scripts/start.ps1", "scripts/setup.sh", "scripts/start.sh", "ganymede-backend/app/cli_preflight.py", "ganymede-backend/app/services/substrate.py", "ganymede-backend/app/services/personas.py"]:
            shutil.copyfile(REPO / relative, self.root / relative)
            self.assertEqual((REPO / relative).read_bytes(), (self.root / relative).read_bytes())
        self.env = os.environ.copy()
        self.env.pop("GANYMEDE_CLAUDE_BIN", None)
        self.env.pop("PYTHONPATH", None)
        self.env.update(PATH=str(self.bin), FIXTURE_LOG=str(self.log), FIXTURE_PYTHON=sys.executable, FIXTURE_FAIL="", FIXTURE_NPM_EXIT="0")
        self.cli = self.root / "synthetic CLI with spaces.exe"
        self.cli.write_text("Synthetic executable path. Never run this file.", encoding="utf-8")
        if os.name == "nt":
            shutil.copyfile(self.native, self.bin / "python.exe")
            (self.bin / "npm.cmd").write_text('@echo off\necho npm %*>>"%FIXTURE_LOG%"\nexit /b %FIXTURE_NPM_EXIT%\n', encoding="ascii")

    def dotenv(self, value: Path) -> None:
        (self.backend / ".env").write_text(f'GANYMEDE_CLAUDE_BIN="{value.as_posix()}"\n', encoding="utf-8")

    def run_ps(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args], cwd=self.root, env=self.env, capture_output=True, text=True, timeout=30)

    @unittest.skipUnless(os.name == "nt", "Windows native exit behavior")
    def test_setup_stops_at_each_native_failure_and_only_reports_actual_success(self) -> None:
        for failure, expected_calls in [("venv", 1), ("upgrade", 2), ("requirements", 3), ("npm", 4), ("", 4)]:
            with self.subTest(failure=failure or "success"):
                venv = self.root / ".venv"
                if venv.exists():
                    shutil.rmtree(venv)
                self.log.unlink(missing_ok=True)
                self.env["FIXTURE_FAIL"] = failure
                self.env["FIXTURE_NPM_EXIT"] = "53" if failure == "npm" else "0"
                result = self.run_ps(self.root / "scripts/setup.ps1")
                self.assertEqual(result.returncode == 0, not failure, result.stdout + result.stderr)
                self.assertEqual("dependencies are installed" in result.stdout, not failure)
                calls = self.log.read_text().splitlines()
                self.assertEqual(len(calls), expected_calls, calls)
                self.assertEqual("npm ci" in calls, failure in ("npm", ""))

    @unittest.skipUnless(os.name == "nt", "Windows py launcher fallback")
    def test_setup_checks_py_fallback_exit(self) -> None:
        (self.bin / "python.exe").rename(self.bin / "py.exe")
        self.env["FIXTURE_FAIL"] = "venv"
        result = self.run_ps(self.root / "scripts/setup.ps1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("dependencies are installed", result.stdout)
        self.assertTrue(self.log.read_text().startswith("-3 -m venv"))

    def test_shared_preflight_loads_dotenv_and_respects_process_precedence(self) -> None:
        self.dotenv(self.cli)
        command = [sys.executable, "-m", "app.cli_preflight"]
        def check(expected: int) -> None:
            result = subprocess.run(command, cwd=self.backend, env=self.env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        check(0)
        self.env["GANYMEDE_CLAUDE_BIN"] = str(self.root / "missing.exe")
        check(1)  # A valid .env must not override an invalid explicit environment value.
        self.env["GANYMEDE_CLAUDE_BIN"] = str(self.cli)
        self.dotenv(self.root / "missing.exe")
        check(0)
        self.env.pop("GANYMEDE_CLAUDE_BIN")
        check(1)
        (self.backend / ".env").unlink()
        check(1)
        path_cli = self.bin / ("claude.exe" if os.name == "nt" else "claude")
        path_cli.write_text("synthetic PATH entry", encoding="utf-8")
        path_cli.chmod(0o755)
        check(0)

    @unittest.skipUnless(os.name == "nt", "Windows launcher integration")
    def test_windows_launcher_uses_real_dotenv_preflight_and_preserves_modes(self) -> None:
        venv = self.root / ".venv/Scripts"
        venv.mkdir(parents=True)
        shutil.copyfile(self.native, venv / "python.exe")
        self.dotenv(self.cli)
        wrapper = self.root / "invoke-start.ps1"
        wrapper.write_text(r'''
param([switch]$Lan)
$ErrorActionPreference = 'Stop'
$global:fixtureCalls = @()
$global:fixtureStopped = @()
function Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle, [switch]$PassThru)
    $global:fixtureCalls += @{ file = $FilePath; args = $ArgumentList; directory = $WorkingDirectory; window = $WindowStyle }
    return [pscustomobject]@{ Id = 10000 + $global:fixtureCalls.Count; HasExited = $false }
}
function Wait-Process { param($Id) }
function Stop-Process { param($Id, [switch]$Force) $global:fixtureStopped += $Id }
$code = 0
try { & (Join-Path $PSScriptRoot 'scripts/start.ps1') -Lan:$Lan }
catch { Write-Output $_; $code = 1 }
@{ calls = @($global:fixtureCalls); stopped = @($global:fixtureStopped) } | ConvertTo-Json -Depth 6 -Compress | Write-Output
exit $code
''', encoding="utf-8")
        for lan in (False, True):
            result = self.run_ps(wrapper, *(["-Lan"] if lan else []))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(len(report["calls"]), 2)
            self.assertEqual(len(report["stopped"]), 2)
            for call in report["calls"]:
                self.assertEqual(call["window"], "Hidden")
                self.assertIn("0.0.0.0" if lan else "127.0.0.1", call["args"])
            self.assertIn("uvicorn", report["calls"][0]["args"])
            self.assertIn("dev", report["calls"][1]["args"])
        self.env["GANYMEDE_CLAUDE_BIN"] = str(self.root / "missing.exe")
        result = self.run_ps(wrapper)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1])["calls"], [])
        shutil.rmtree(self.root / ".venv")
        result = self.run_ps(self.root / "scripts/start.ps1", "-Showcase")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("npm run dev:showcase -- --hostname 127.0.0.1", self.log.read_text())
        # The fixture only executed preflight and the inert showcase npm command.
        self.assertNotIn("uvicorn", self.log.read_text())

    @unittest.skipUnless(SHELL, "POSIX shell is unavailable")
    def test_posix_syntax_and_launch_preflight(self) -> None:
        for script in ("setup.sh", "start.sh"):
            subprocess.run([SHELL, "-n", str(self.root / "scripts" / script)], check=True, capture_output=True, text=True)
        venv = self.root / ".venv/bin"
        venv.mkdir(parents=True)
        python = venv / "python"
        python.write_text(
            '#!/bin/sh\nif [ "$2" = "app.cli_preflight" ]; then\n'
            f'  exec "{Path(sys.executable).as_posix()}" "$@"\nfi\n'
            'printf "%s\\n" "python $*" >> "$FIXTURE_LOG"\n', encoding="utf-8")
        python.chmod(0o755)
        npm = self.bin / "npm"
        npm.write_text('#!/bin/sh\nprintf "%s\\n" "npm $*" >> "$FIXTURE_LOG"\n', encoding="utf-8")
        npm.chmod(0o755)
        if os.name == "nt":
            self.env["PATH"] = f"{self.bin};C:/Program Files/Git/usr/bin"
        else:
            self.env["PATH"] = f"{self.bin}:/usr/bin:/bin"
        self.dotenv(self.cli)
        command = [SHELL, str(self.root / "scripts/start.sh")]
        result = subprocess.run(command, cwd=self.root, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("npm run dev -- --hostname 127.0.0.1", self.log.read_text())
        self.log.unlink()
        self.env["GANYMEDE_CLAUDE_BIN"] = str(self.root / "missing.exe")
        result = subprocess.run(command, cwd=self.root, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())
        shutil.rmtree(self.root / ".venv")
        result = subprocess.run([*command, "showcase"], cwd=self.root, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("npm run dev:showcase -- --hostname 127.0.0.1", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
