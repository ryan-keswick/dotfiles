"""Check portable shell initialization with isolated homes and fake tools."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ZSH = shutil.which("zsh")
ZSHRC = Path(__file__).resolve().parents[1] / ".zshrc"

MOCK_TOOL = r"""
import os
from pathlib import Path
import shlex
import sys

tool = Path(sys.argv[0]).name
args = sys.argv[1:]
if tool == "uname":
    print(os.environ["DOTFILES_TEST_OS"])
elif tool == "brew":
    if args == ["shellenv"]:
        print("export HOMEBREW_PREFIX=" + shlex.quote(os.environ["DOTFILES_TEST_PREFIX"]))
        print('export BREW_INIT_COUNT=$(( ${BREW_INIT_COUNT:-0} + 1 ))')
    elif args == ["--prefix"]:
        print(os.environ["DOTFILES_TEST_PREFIX"])
    else:
        raise SystemExit("Unexpected brew arguments")
elif tool == "pyenv" and args == ["init", "-", "zsh"]:
    print('export PYENV_INIT_COUNT=$(( ${PYENV_INIT_COUNT:-0} + 1 ))')
elif tool == "starship" and args == ["init", "zsh"]:
    print('export STARSHIP_INIT_COUNT=$(( ${STARSHIP_INIT_COUNT:-0} + 1 ))')
else:
    raise SystemExit("Unexpected shell initialization command")
"""


@unittest.skipUnless(ZSH, "zsh is required for shell initialization checks")
class ZshrcTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="dotfiles shell tests ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home with spaces"
        self.bin = self.root / "mock bin"
        self.prefix = self.root / "brew prefix"
        for directory in (self.home, self.bin, self.prefix):
            directory.mkdir()
        self.env = {
            "HOME": str(self.home),
            "PATH": str(self.bin),
            "LC_ALL": "C",
            "DOTFILES_TEST_OS": "Linux",
            "DOTFILES_TEST_PREFIX": str(self.prefix),
        }
        self.mock = self.root / "mock-tool"
        self.mock.write_text("#!/usr/bin/env python3\n" + MOCK_TOOL)
        self.mock.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        self.install_tools("uname")

    def install_tools(self, *tools):
        for tool in tools:
            (self.bin / tool).symlink_to(self.mock)

    def write_nvm(self, directory, source):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "nvm.sh").write_text(
            "export NVM_INIT_COUNT=$(( ${NVM_INIT_COUNT:-0} + 1 ))\n"
            f"export NVM_SOURCE={source}\n"
        )

    def run_shell(self, *, repeat=False, **overrides):
        env = {**self.env, **overrides}
        # Mac tests provide a fake brew, so fixed fallback paths are never used.
        if env["DOTFILES_TEST_OS"] == "Darwin" and not (self.bin / "brew").exists():
            self.fail("Mac shell tests must mock Homebrew")
        program = 'source "$1"\n'
        if repeat:
            program += 'source "$1"\n'
        program += '"$2" -c "import json, os; print(json.dumps(dict(os.environ)))"\n'
        result = subprocess.run(
            [ZSH, "-dfc", program, "shell-test", str(ZSHRC), sys.executable],
            env=env,
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_missing_optional_tools_are_safe_on_linux(self):
        result = self.run_shell()
        self.assertEqual(result["NVM_DIR"], str(self.home / ".nvm"))
        self.assertNotIn("PYENV_ROOT", result)
        self.assertNotIn("STARSHIP_INIT_COUNT", result)
        self.assertNotIn("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", result)

    def test_mac_initializes_available_tools_once(self):
        self.install_tools("brew", "pyenv", "starship")
        self.write_nvm(self.prefix / "opt/nvm", "homebrew")
        result = self.run_shell(DOTFILES_TEST_OS="Darwin")
        for key in (
            "BREW_INIT_COUNT",
            "PYENV_INIT_COUNT",
            "STARSHIP_INIT_COUNT",
            "NVM_INIT_COUNT",
        ):
            self.assertEqual(result[key], "1")
        self.assertEqual(result["NVM_SOURCE"], "homebrew")
        self.assertEqual(result["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"], "YES")

    def test_mac_with_brew_but_without_optional_tools_is_safe(self):
        self.install_tools("brew")
        result = self.run_shell(DOTFILES_TEST_OS="Darwin")
        self.assertNotIn("NVM_INIT_COUNT", result)
        self.assertNotIn("PYENV_INIT_COUNT", result)
        self.assertNotIn("STARSHIP_INIT_COUNT", result)

    def test_upstream_nvm_takes_precedence_over_homebrew(self):
        self.install_tools("brew")
        self.write_nvm(self.home / ".nvm", "upstream")
        self.write_nvm(self.prefix / "opt/nvm", "homebrew")
        result = self.run_shell(DOTFILES_TEST_OS="Darwin")
        self.assertEqual(result["NVM_SOURCE"], "upstream")
        self.assertEqual(result["NVM_INIT_COUNT"], "1")

    def test_custom_runtime_directories_are_preserved(self):
        self.install_tools("brew", "pyenv")
        custom_nvm = self.root / "custom node versions"
        custom_pyenv = self.root / "custom python versions"
        self.write_nvm(custom_nvm, "custom")
        (custom_pyenv / "bin").mkdir(parents=True)
        result = self.run_shell(
            DOTFILES_TEST_OS="Darwin",
            NVM_DIR=str(custom_nvm),
            PYENV_ROOT=str(custom_pyenv),
        )
        self.assertEqual(result["NVM_DIR"], str(custom_nvm))
        self.assertEqual(result["NVM_SOURCE"], "custom")
        self.assertEqual(result["PYENV_ROOT"], str(custom_pyenv))
        self.assertIn(str(custom_pyenv / "bin"), result["PATH"].split(os.pathsep))

    def test_empty_upstream_nvm_loader_falls_back_to_homebrew(self):
        self.install_tools("brew")
        (self.home / ".nvm").mkdir()
        (self.home / ".nvm/nvm.sh").touch()
        self.write_nvm(self.prefix / "opt/nvm", "homebrew")
        result = self.run_shell(DOTFILES_TEST_OS="Darwin")
        self.assertEqual(result["NVM_SOURCE"], "homebrew")

    def test_xdg_nvm_directory_is_used_without_an_explicit_override(self):
        config = self.root / "custom config"
        self.write_nvm(config / "nvm", "xdg")
        result = self.run_shell(XDG_CONFIG_HOME=str(config))
        self.assertEqual(result["NVM_DIR"], str(config / "nvm"))
        self.assertEqual(result["NVM_SOURCE"], "xdg")

    def test_inherited_authentication_values_are_preserved(self):
        result = self.run_shell(
            GITHUB_TOKEN="existing-github-value", NPM_TOKEN="existing-npm-value"
        )
        self.assertEqual(result["GITHUB_TOKEN"], "existing-github-value")
        self.assertEqual(result["NPM_TOKEN"], "existing-npm-value")

    def test_local_configuration_runs_last(self):
        self.install_tools("starship")
        (self.home / ".zshrc.local").write_text(
            'export LOCAL_OBSERVED_STARSHIP="$STARSHIP_INIT_COUNT"\n'
            "export NPM_TOKEN=local-value\n"
        )
        result = self.run_shell(NPM_TOKEN="inherited-value")
        self.assertEqual(result["LOCAL_OBSERVED_STARSHIP"], "1")
        self.assertEqual(result["NPM_TOKEN"], "local-value")

    def test_repeated_sourcing_does_not_duplicate_path_entries(self):
        result = self.run_shell(repeat=True)
        entries = result["PATH"].split(os.pathsep)
        self.assertEqual(entries.count(str(self.home / ".local/bin")), 1)
        self.assertNotIn("/home/coder/.local/bin", entries)


if __name__ == "__main__":
    unittest.main()
