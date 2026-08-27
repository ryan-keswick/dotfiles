# Personal dotfiles

Shared shell, editor, terminal, and tmux configuration, with a macOS bootstrap
for personal and work Macs. The Mac setup does not depend on a devbox checkout.

## Set up a Mac

Install Xcode Command Line Tools with `xcode-select --install`, then clone this
repository anywhere you want to keep it. The Neovim submodule uses GitHub SSH,
so configure access to the repository listed in `.gitmodules` before setup.

Run the script as your normal user, from any directory:

```bash
/path/to/dotfiles/mac_setup.sh
```

Setup finds an existing Homebrew installation, or downloads its official
installer if none exists. Homebrew may request administrator approval.
It installs the packages in `Brewfile`, optional applications in
`Brewfile.apps`, Node 24 from `.nvmrc`, and Python 3.12 through pyenv. The Node
major and Python minor select their latest available patch releases; these
are not exact version locks. Set an exact version in `.nvmrc` or through
`MAC_SETUP_PYTHON_VERSION` if needed.

Configuration is linked directly to this checkout, including the Neovim
submodule. Keep the checkout in place. Existing correct links are left alone.
Conflicting files, directories, or links stop setup before package installation.
Review the reported paths, then rerun with `--backup` to move conflicts into a
unique directory under `~/.dotfiles-backups/` before linking. Existing local
files are never silently adopted into the repository. A symlinked parent
directory that would redirect new links into another checkout is refused.
To restore a backup, remove the corresponding new link and move the saved
entry back to its original path. Backed-up relative symlinks may not resolve
inside the backup directory; their original targets are unchanged.
Tmux plugins are installed through a temporary, sessionless server; existing
tmux sessions are not reconfigured or stopped.

Useful options:

```bash
./mac_setup.sh --backup
./mac_setup.sh --skip-apps
./mac_setup.sh --upgrade
./mac_setup.sh --set-python-default
MAC_SETUP_PYTHON_VERSION=3.13 ./mac_setup.sh --skip-apps
```

Options can be combined. `--skip-apps` omits Slack, Spotify, and Docker Desktop;
command-line tools and the terminal font are still installed. Docker Desktop
provides the Docker CLI, so the separate Docker formula is not installed.
Existing applications managed outside Homebrew can be kept by using
`--skip-apps`. There is no forced cask adoption or package cleanup.

Normal setup uses `brew bundle install --no-upgrade` and never runs a blanket
`brew upgrade`. Homebrew can still update dependencies needed for an install.
`--upgrade` explicitly upgrades packages from the manifests. Python's global
selection is left unchanged unless `--set-python-default` is provided. NVM
keeps an existing default and initializes one for its first Node installation.

Shell setup supports Intel and Apple Silicon Homebrew locations, upstream or
Homebrew NVM, and optional tools that have not yet been installed. Put local
aliases and other machine-specific settings in `~/.zshrc.local`, which is sourced
last and is not tracked here. Set `NVM_DIR`, `PYENV_ROOT`, or `XDG_CONFIG_HOME`
before starting setup and the shell if you use custom installation paths.

## Check changes

```bash
bash -n mac_setup.sh
zsh -n .zshrc
python3 -m unittest discover -s tests -v
```

The tests use disposable homes and mocked package managers. They do not install
software or replace your real configuration. They cover fresh installs,
repeated runs, conflicts and backups, and failures. Actual package installation
still needs validation on a Mac.

The bootstrap, manifests, runtime selection, and tests are excluded from Stow
when this repository is consumed as a package by another dotfiles repository.
