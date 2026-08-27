"""Exercise the macOS bootstrap without installing tools or touching a real home."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")

MOCK_COMMAND = r"""
import json
import os
from pathlib import Path
import shlex
import sys

tool = Path(sys.argv[0]).name
args = sys.argv[1:]
if tool == "mac-setup-test-nvm":
    tool = "nvm"
with open(os.environ["MAC_SETUP_TEST_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"tool": tool, "args": args, "tmux": os.environ.get("TMUX", "")}) + "\n")

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(42)

def executable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)

prefix = Path(os.environ["MAC_SETUP_TEST_BREW_PREFIX"])
failure = os.environ.get("MAC_SETUP_TEST_FAIL", "")

if tool == "uname":
    print("arm64" if "-m" in args else os.environ.get("MAC_SETUP_TEST_OS", "Darwin"))
elif tool == "xcode-select":
    if failure == "xcode-select":
        fail("Command Line Tools are not installed")
    print(os.environ["MAC_SETUP_TEST_CLT"])
elif tool == "brew":
    if args and args[0] == "--prefix":
        print(prefix / "opt" / args[1] if len(args) > 1 else prefix)
    elif args and args[0] == "shellenv":
        print("export HOMEBREW_PREFIX=" + shlex.quote(str(prefix)))
    elif args and args[0] == "bundle":
        if failure == "brew":
            fail("mock Homebrew bundle failure")
    else:
        fail("Unexpected Homebrew command: " + repr(args))
elif tool == "git":
    while args[:1] == ["-C"]:
        args = args[2:]
    if args[:1] == ["submodule"]:
        if failure == "git":
            fail("mock submodule checkout failure")
    elif args[:1] == ["clone"]:
        if failure == "git-clone":
            fail("mock plugin checkout failure")
        destination = Path(args[-1])
        if destination.exists() and any(destination.iterdir()):
            fail("clone destination already exists")
        (destination / ".git").mkdir(parents=True)
        executable(destination / "bin" / "install_plugins",
                   "#!/usr/bin/env bash\nmac-setup-test-plugins\n")
        executable(destination / "tpm", "#!/usr/bin/env bash\nexit 0\n")
    elif args[:1] == ["rev-parse"]:
        if "--is-inside-work-tree" in args:
            print("true")
        else:
            print(os.environ["MAC_SETUP_TEST_REPO"])
    else:
        fail("Unexpected Git command: " + repr(args))
elif tool == "nvm":
    if failure == "nvm" or (failure == "nvm-exec" and args[:1] == ["exec"]):
        fail("mock Node installation failure")
elif tool == "pyenv":
    if args[:1] == ["install"]:
        if failure == "pyenv":
            fail("mock Python installation failure")
    elif args[:1] == ["global"]:
        version_file = Path(os.environ.get("PYENV_ROOT", str(Path.home() / ".pyenv"))) / "version"
        if len(args) > 1:
            version_file.parent.mkdir(parents=True, exist_ok=True)
            version_file.write_text("\n".join(args[1:]) + "\n", encoding="utf-8")
        else:
            print(version_file.read_text().strip() if version_file.exists() else "system")
    elif args[:1] == ["root"]:
        print(Path.home() / ".pyenv")
    elif args[:1] == ["exec"]:
        if failure == "pyenv-exec":
            fail("mock Python verification failure")
        print("Python " + os.environ.get("PYENV_VERSION", "3.12"))
    else:
        fail("Unexpected pyenv command: " + repr(args))
elif tool in ("tmux", "nvim", "mac-setup-test-plugins"):
    if tool == "tmux" and failure == "tmux-start" and "start-server" in args:
        fail("mock tmux startup failure")
    if tool == "mac-setup-test-plugins" and failure == "plugins":
        fail("mock plugin installation failure")
elif tool in ("curl", "sudo"):
    if tool == "curl" and os.environ.get("MAC_SETUP_TEST_SENTRY") and "--output" in args:
        destination = Path(args[args.index("--output") + 1])
        destination.write_text("printf executed > " + shlex.quote(os.environ["MAC_SETUP_TEST_SENTRY"]) + "\n")
    fail("Unexpected installer invocation blocked: " + tool)
else:
    fail("Unexpected mock command: " + tool)
"""


class MacSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac setup tests ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "checkout with spaces" / "dotfiles"
        self.home = self.root / "home with spaces"
        self.cwd = self.root / "unrelated working directory"
        self.bin = self.root / "mock bin"
        self.prefix = self.root / "Homebrew prefix"
        self.log = self.root / "commands.jsonl"
        self.clt = self.root / "Command Line Tools"
        for directory in (
            self.repo,
            self.home,
            self.cwd,
            self.bin,
            self.prefix,
            self.clt,
        ):
            directory.mkdir(parents=True)
        self.log.touch()
        shutil.copy2(REPO_ROOT / "mac_setup.sh", self.repo / "mac_setup.sh")

        self.configs = {
            ".zshrc": "export EXAMPLE_SETTING=1\n",
            ".vimrc": "set number\n",
            ".tflint.hcl": "config {}\n",
            ".config/nvim/init.lua": "vim.opt.number = true\n",
            ".config/tmux/tmux.conf": "set -g mouse on\n",
            ".config/alacritty/alacritty.toml": "[window]\nopacity = 1.0\n",
            ".config/starship.toml": "add_newline = false\n",
        }
        for name, contents in self.configs.items():
            self.write(self.repo / name, contents)
        self.write(self.repo / "Brewfile", 'brew "nvm"\nbrew "pyenv"\n')
        self.write(self.repo / "Brewfile.apps", 'cask "alacritty"\n')
        self.write(self.repo / ".nvmrc", "24\n")
        self.write(
            self.repo / ".gitmodules",
            '[submodule ".config/nvim"]\n\tpath = .config/nvim\n',
        )
        (self.repo / ".git").mkdir()

        mock = self.bin / "mock-command"
        self.write(mock, "#!/usr/bin/env python3\n" + textwrap.dedent(MOCK_COMMAND))
        mock.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        for command in (
            "brew",
            "git",
            "uname",
            "xcode-select",
            "pyenv",
            "tmux",
            "nvim",
            "curl",
            "sudo",
            "mac-setup-test-nvm",
            "mac-setup-test-plugins",
        ):
            (self.bin / command).symlink_to(mock)

        # Only these real utilities are available; all installation tools are mocked.
        for command in (
            "awk",
            "basename",
            "bash",
            "cat",
            "chmod",
            "cmp",
            "cp",
            "cut",
            "date",
            "dirname",
            "env",
            "find",
            "grep",
            "head",
            "id",
            "ln",
            "ls",
            "mkdir",
            "mktemp",
            "mv",
            "printf",
            "pwd",
            "readlink",
            "realpath",
            "rm",
            "sed",
            "sort",
            "tail",
            "test",
            "touch",
            "tr",
            "wc",
        ):
            executable = shutil.which(command)
            if executable:
                (self.bin / command).symlink_to(executable)
        (self.prefix / "bin").mkdir()
        (self.prefix / "bin" / "brew").symlink_to(mock)
        self.write(
            self.prefix / "opt" / "nvm" / "nvm.sh",
            'nvm() { mac-setup-test-nvm "$@"; }\n',
        )

        self.env = {
            "HOME": str(self.home),
            "PATH": str(self.bin),
            "TMPDIR": str(self.root),
            "SHELL": str(BASH),
            "LC_ALL": "C",
            "MAC_SETUP_TEST_LOG": str(self.log),
            "MAC_SETUP_TEST_REPO": str(self.repo),
            "MAC_SETUP_TEST_BREW_PREFIX": str(self.prefix),
            "MAC_SETUP_TEST_CLT": str(self.clt),
        }

    @staticmethod
    def write(path, contents):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def run_setup(self, *args, entrypoint=None, **env_overrides):
        return subprocess.run(
            [BASH, str(entrypoint or self.repo / "mac_setup.sh"), *args],
            cwd=self.cwd,
            env={**self.env, **env_overrides},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=15,
            check=False,
        )

    def calls(self, tool=None):
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return [call for call in calls if tool is None or call["tool"] == tool]

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout)

    def assert_config_links(self, config_dir=None):
        for relative in (
            ".zshrc",
            ".vimrc",
            ".tflint.hcl",
            ".config/nvim",
            ".config/tmux",
            ".config/alacritty",
            ".config/starship.toml",
        ):
            with self.subTest(config=relative):
                destination = self.home / relative
                if config_dir is not None and relative.startswith(".config/"):
                    destination = config_dir / Path(relative).relative_to(".config")
                self.assertTrue(destination.is_symlink(), str(destination))
                self.assertEqual(
                    destination.resolve(), (self.repo / relative).resolve()
                )

    def assert_no_installations(self):
        for call in self.calls():
            tool, args = call["tool"], call["args"]
            self.assertNotIn(
                tool, ("curl", "sudo", "nvm", "mac-setup-test-plugins"), call
            )
            self.assertFalse(tool == "brew" and args[:1] == ["bundle"], call)
            self.assertFalse(tool == "pyenv" and args[:1] == ["install"], call)
            self.assertFalse(tool == "git" and "clone" in args, call)

    def assert_private_tmux_server_is_cleaned_up(self):
        commands = [
            call["args"] for call in self.calls("tmux") if call["args"] != ["-V"]
        ]
        starts = [args for args in commands if "start-server" in args]
        stops = [args for args in commands if "kill-server" in args]
        self.assertEqual(len(starts), 1, commands)
        self.assertEqual(len(stops), 1, commands)
        self.assertEqual(starts[0][:1], ["-S"])
        socket = Path(starts[0][1])
        self.assertEqual(socket.name, "tmux.sock")
        self.assertEqual(socket.parent.parent, self.root)
        self.assertTrue(socket.parent.name.startswith("mac-setup."), socket)
        self.assertIn("-f", starts[0])
        self.assertEqual(starts[0][starts[0].index("-f") + 1], "/dev/null")
        for args in commands:
            self.assertEqual(args[:2], ["-S", str(socket)], args)
        self.assertEqual(commands[-1], ["-S", str(socket), "kill-server"])
        for installer in self.calls("mac-setup-test-plugins"):
            self.assertEqual(installer["tmux"], str(socket) + ",0,0")
        self.assertEqual(list(self.root.glob("mac-setup.*")), [])
        return socket

    def test_help_does_not_require_macos(self):
        result = self.run_setup("--help", MAC_SETUP_TEST_OS="Linux")
        self.assert_success(result)
        for option in ("--skip-apps", "--backup", "--upgrade", "--set-python-default"):
            self.assertIn(option, result.stdout)
        self.assert_no_installations()

    def test_rejects_linux_before_installing(self):
        result = self.run_setup(MAC_SETUP_TEST_OS="Linux")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_no_installations()
        self.assertFalse((self.home / ".zshrc").exists())

    def test_rejects_missing_command_line_tools(self):
        result = self.run_setup(MAC_SETUP_TEST_FAIL="xcode-select")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_no_installations()

    def test_fresh_install_from_another_directory_with_spaces(self):
        result = self.run_setup()
        self.assert_success(result)
        self.assert_config_links()
        bundles = [
            call["args"]
            for call in self.calls("brew")
            if call["args"][:1] == ["bundle"]
        ]
        self.assertEqual(len(bundles), 2, bundles)
        self.assertTrue(all("--no-upgrade" in args for args in bundles), bundles)
        self.assertFalse(
            any(call["args"][:1] == ["upgrade"] for call in self.calls("brew"))
        )
        self.assertTrue(
            any(
                "submodule" in call["args"] and "--recursive" in call["args"]
                for call in self.calls("git")
            )
        )
        self.assertTrue(
            any(
                call["args"][:1] == ["install"] and "24" in call["args"]
                for call in self.calls("nvm")
            )
        )
        self.assertTrue(
            any(
                call["args"][:1] == ["install"] and "--skip-existing" in call["args"]
                for call in self.calls("pyenv")
            )
        )
        self.assertFalse(self.calls("curl"))
        self.assertFalse(self.calls("sudo"))
        self.assertEqual(list(self.cwd.iterdir()), [])

    def test_second_run_keeps_links_and_does_not_clone_tpm_again(self):
        self.assert_success(self.run_setup())
        self.log.write_text("")
        result = self.run_setup()
        self.assert_success(result)
        self.assert_config_links()
        self.assertFalse(any("clone" in call["args"] for call in self.calls("git")))
        self.assertFalse((self.home / ".dotfiles-backups").exists())
        for relative, contents in self.configs.items():
            self.assertEqual((self.repo / relative).read_text(), contents)

    def test_invocation_through_relative_script_symlink(self):
        entrypoint = self.cwd / "setup link"
        entrypoint.symlink_to(os.path.relpath(self.repo / "mac_setup.sh", self.cwd))
        result = self.run_setup(entrypoint=entrypoint)
        self.assert_success(result)
        self.assert_config_links()

    def test_absolute_xdg_configuration_override(self):
        config_dir = self.root / "custom configuration directory"
        result = self.run_setup(XDG_CONFIG_HOME=str(config_dir))
        self.assert_success(result)
        self.assert_config_links(config_dir)
        self.assertTrue((config_dir / "nvm").is_dir())
        self.assertFalse((self.home / ".config").exists())

    def test_existing_configuration_stops_before_installing(self):
        original = "keep my existing shell configuration\n"
        self.write(self.home / ".zshrc", original)
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.home / ".zshrc").read_text(), original)
        self.assertFalse((self.home / ".zshrc").is_symlink())
        self.assertIn("--backup", result.stdout)
        self.assert_no_installations()

    def test_conflicting_parent_stops_before_installing(self):
        original = "preserve this file occupying the configuration directory\n"
        self.write(self.home / ".config", original)
        result = self.run_setup("--backup")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.home / ".config").read_text(), original)
        self.assert_no_installations()

    def test_symlinked_parent_is_preserved_without_installing(self):
        shared = self.root / "separately managed configuration"
        self.write(shared / "keep.txt", "do not change this directory\n")
        (self.home / ".config").symlink_to(shared, target_is_directory=True)
        result = self.run_setup("--backup")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue((self.home / ".config").is_symlink())
        self.assertEqual(list(shared.iterdir()), [shared / "keep.txt"])
        self.assert_no_installations()

    @unittest.skipIf(os.geteuid() == 0, "root bypasses directory write permissions")
    def test_readonly_parent_stops_before_installing(self):
        parent = self.home / ".config"
        parent.mkdir()
        parent.chmod(0o500)
        self.addCleanup(parent.chmod, 0o700)
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_no_installations()

    def test_backup_preserves_conflicting_files_and_directories(self):
        originals = {
            ".zshrc": "keep my existing shell configuration\n",
            ".config/nvim/init.lua": "-- preserve existing editor configuration\n",
            ".config/nvim/lua/options.lua": "-- preserve nested editor configuration\n",
        }
        for relative, contents in originals.items():
            self.write(self.home / relative, contents)
        result = self.run_setup("--backup")
        self.assert_success(result)
        self.assert_config_links()
        backups = list((self.home / ".dotfiles-backups").glob("mac-setup.*"))
        self.assertEqual(len(backups), 1, backups)
        saved = [path.read_text() for path in backups[0].rglob("*") if path.is_file()]
        for contents in originals.values():
            self.assertIn(contents, saved)

    def test_backup_moves_conflicting_symlink_without_changing_its_target(self):
        original_target = self.root / "previous shell configuration"
        self.write(original_target, "keep this separately managed configuration\n")
        (self.home / ".zshrc").symlink_to(original_target)
        result = self.run_setup("--backup")
        self.assert_success(result)
        self.assert_config_links()
        self.assertEqual(
            original_target.read_text(), "keep this separately managed configuration\n"
        )
        saved_links = [
            path
            for path in (self.home / ".dotfiles-backups").rglob("*")
            if path.is_symlink()
        ]
        self.assertTrue(
            any(path.resolve() == original_target for path in saved_links), saved_links
        )

    def test_later_backup_does_not_overwrite_previous_backup(self):
        self.write(self.home / ".zshrc", "first configuration\n")
        self.assert_success(self.run_setup("--backup"))
        (self.home / ".zshrc").unlink()
        self.write(self.home / ".zshrc", "second configuration\n")
        self.assert_success(self.run_setup("--backup"))
        backups = list((self.home / ".dotfiles-backups").glob("mac-setup.*"))
        self.assertEqual(len(backups), 2, backups)
        saved = [
            path.read_text()
            for backup in backups
            for path in backup.rglob("*")
            if path.is_file()
        ]
        self.assertIn("first configuration\n", saved)
        self.assertIn("second configuration\n", saved)

    def test_skip_apps_only_installs_core_manifest(self):
        result = self.run_setup("--skip-apps")
        self.assert_success(result)
        bundles = [
            call["args"]
            for call in self.calls("brew")
            if call["args"][:1] == ["bundle"]
        ]
        self.assertEqual(len(bundles), 1, bundles)
        self.assertFalse(any("Brewfile.apps" in arg for arg in bundles[0]))

    def test_upgrade_is_limited_to_manifests(self):
        result = self.run_setup("--upgrade")
        self.assert_success(result)
        calls = [call["args"] for call in self.calls("brew")]
        self.assertFalse(any(args[:1] == ["upgrade"] for args in calls), calls)
        bundles = [args for args in calls if args[:1] == ["bundle"]]
        self.assertEqual(len(bundles), 2, bundles)
        self.assertTrue(all("--no-upgrade" not in args for args in bundles), bundles)
        self.assertTrue(
            all(any("--file" in arg for arg in args) for args in bundles), bundles
        )

    def test_preserves_existing_python_default(self):
        version_file = self.home / ".pyenv" / "version"
        self.write(version_file, "3.11.9\n")
        result = self.run_setup()
        self.assert_success(result)
        self.assertEqual(version_file.read_text(), "3.11.9\n")
        self.assertFalse(
            any(
                call["args"][:1] == ["global"] and len(call["args"]) > 1
                for call in self.calls("pyenv")
            )
        )

    def test_explicit_python_default_uses_configured_version(self):
        result = self.run_setup(
            "--set-python-default", MAC_SETUP_PYTHON_VERSION="3.13.5"
        )
        self.assert_success(result)
        self.assertEqual((self.home / ".pyenv" / "version").read_text(), "3.13.5\n")
        self.assertTrue(
            any(
                "3.13.5" in call["args"] and "install" in call["args"]
                for call in self.calls("pyenv")
            )
        )

    def test_dependency_failures_return_nonzero(self):
        for tool in ("brew", "git", "nvm", "nvm-exec", "pyenv", "pyenv-exec"):
            with self.subTest(tool=tool):
                self.log.write_text("")
                result = self.run_setup(MAC_SETUP_TEST_FAIL=tool)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertTrue(self.calls(tool.split("-")[0]), result.stdout)

    def test_failed_tpm_checkout_cleans_temporary_directory(self):
        result = self.run_setup(MAC_SETUP_TEST_FAIL="git-clone")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.home / ".tmux" / "plugins" / "tpm").exists())
        self.assertEqual(list(self.root.glob("mac-setup.*")), [])

    def test_plugin_installer_uses_private_server_inside_existing_tmux(self):
        existing_socket = self.root / "existing user tmux.sock"
        self.write(existing_socket, "preserve the existing server\n")
        incoming_tmux = str(existing_socket) + ",123,1"
        result = self.run_setup(TMUX=incoming_tmux)
        self.assert_success(result)
        self.assertEqual(len(self.calls("mac-setup-test-plugins")), 1)
        socket = self.assert_private_tmux_server_is_cleaned_up()
        self.assertNotEqual(socket, existing_socket)
        self.assertNotEqual(
            self.calls("mac-setup-test-plugins")[0]["tmux"], incoming_tmux
        )
        self.assertEqual(existing_socket.read_text(), "preserve the existing server\n")

    def test_plugin_failure_stops_private_server_and_cleans_temporary_directory(self):
        result = self.run_setup(MAC_SETUP_TEST_FAIL="plugins")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.calls("mac-setup-test-plugins")), 1)
        self.assert_private_tmux_server_is_cleaned_up()
        self.assertFalse(self.calls("nvim"))

    def test_tmux_startup_failure_attempts_private_server_cleanup(self):
        result = self.run_setup(MAC_SETUP_TEST_FAIL="tmux-start")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.calls("mac-setup-test-plugins"))
        self.assert_private_tmux_server_is_cleaned_up()
        self.assertFalse(self.calls("nvim"))

    @unittest.skipIf(
        any(
            os.access(path, os.X_OK)
            for path in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew")
        ),
        "a system Homebrew installation would bypass the mocked download",
    )
    def test_failed_homebrew_download_is_never_executed(self):
        (self.bin / "brew").unlink()
        sentry = self.root / "download was executed"
        result = self.run_setup(MAC_SETUP_TEST_SENTRY=str(sentry))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(sentry.exists())
        self.assertEqual(len(self.calls("curl")), 1)
        self.assertIn("--fail", self.calls("curl")[0]["args"])
        self.assertEqual(list(self.root.glob("mac-setup.*")), [])

    def test_missing_neovim_submodule_is_not_linked(self):
        (self.repo / ".config" / "nvim" / "init.lua").unlink()
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.home / ".config" / "nvim").is_symlink())


if __name__ == "__main__":
    unittest.main()
