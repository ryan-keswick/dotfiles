#!/usr/bin/env bash

set -Eeuo pipefail

step="initialization"
setup_tmp_dir=""
tmux_socket=""
backup_dir=""
skip_apps=false
backup_conflicts=false
upgrade_packages=false
set_python_default=false
python_version="${MAC_SETUP_PYTHON_VERSION:-3.12}"

log() { printf '%s\n' "$*"; }
die() { printf 'mac_setup.sh: %s\n' "$*" >&2; exit 1; }

cleanup() {
  if [[ -n "$tmux_socket" ]]; then
    tmux -S "$tmux_socket" kill-server >/dev/null 2>&1 || true
  fi
  if [[ -n "$setup_tmp_dir" ]]; then
    rm -rf -- "$setup_tmp_dir"
  fi
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
trap 'printf "mac_setup.sh: failed during %s (line %s). Fix the error above and rerun.\n" "$step" "$LINENO" >&2' ERR

usage() {
  cat <<'USAGE'
Usage: mac_setup.sh [options]

Install personal tools and link this checkout's configuration on macOS.
Existing configuration is never replaced without --backup.

  --backup              Back up conflicting configs before linking them
  --skip-apps           Skip Slack, Spotify, and Docker Desktop
  --upgrade             Upgrade packages listed in the Brewfiles
  --set-python-default  Select the installed Python version globally
  --help                Show this help

Node is selected by .nvmrc. Python defaults to 3.12; override it with
MAC_SETUP_PYTHON_VERSION. Existing Python defaults are otherwise preserved.
USAGE
}

for option in "$@"; do
  case "$option" in
    --backup) backup_conflicts=true ;;
    --skip-apps) skip_apps=true ;;
    --upgrade) upgrade_packages=true ;;
    --set-python-default) set_python_default=true ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; die "Unknown option: $option" ;;
  esac
done

step="preflight checks"
[[ "$(uname -s)" == Darwin ]] || die "This script only supports macOS."
[[ "$EUID" != 0 ]] || die "Run this script as your normal user, not with sudo."
[[ -n "${HOME:-}" && "$HOME" == /* && "$HOME" != / ]] || die "HOME must be an absolute user directory."
xcode-select -p >/dev/null 2>&1 || die "Install Xcode Command Line Tools with 'xcode-select --install', then rerun."

# Resolve the checkout even when invoked from another directory or a symlink.
script_path="${BASH_SOURCE[0]}"
while [[ -L "$script_path" ]]; do
  script_dir="$(cd -P -- "$(dirname "$script_path")" && pwd)"
  script_path="$(readlink "$script_path")"
  [[ "$script_path" == /* ]] || script_path="$script_dir/$script_path"
done
dotfiles_dir="$(cd -P -- "$(dirname "$script_path")" && pwd)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
[[ "$config_dir" == /* ]] || die "XDG_CONFIG_HOME must be an absolute path."

config_sources=(.zshrc .vimrc .tflint.hcl .config/nvim .config/tmux .config/alacritty .config/starship.toml)
config_targets=("$HOME/.zshrc" "$HOME/.vimrc" "$HOME/.tflint.hcl" "$config_dir/nvim" "$config_dir/tmux" "$config_dir/alacritty" "$config_dir/starship.toml")

# Refuse conflicts before installing packages. Do not write through a symlink
# into another checkout when an existing configuration manages a parent path.
has_conflicts=false
for index in "${!config_sources[@]}"; do
  source_path="$dotfiles_dir/${config_sources[$index]}"
  target_path="${config_targets[$index]}"
  if [[ "$source_path" -ef "$target_path" ]]; then
    continue
  fi
  parent_path="$(dirname "$target_path")"
  while [[ "$parent_path" != "$HOME" && "$parent_path" != / ]]; do
    [[ ! -L "$parent_path" ]] || die "Refusing to write through symlinked parent: $parent_path"
    [[ ! -e "$parent_path" || -d "$parent_path" ]] || die "Configuration parent is not a directory: $parent_path"
    parent_path="$(dirname "$parent_path")"
  done
  writable_parent="$(dirname "$target_path")"
  while [[ ! -d "$writable_parent" && "$writable_parent" != / ]]; do
    writable_parent="$(dirname "$writable_parent")"
  done
  [[ -w "$writable_parent" && -x "$writable_parent" ]] || die "Configuration parent is not writable/searchable: $writable_parent"
  if [[ -e "$target_path" || -L "$target_path" ]]; then
    log "Existing configuration: $target_path"
    has_conflicts=true
  fi
done
if $has_conflicts && ! $backup_conflicts; then
  die "Configuration conflicts found. Rerun with --backup to preserve them in ~/.dotfiles-backups before linking."
fi

make_temp_dir() {
  if [[ -z "$setup_tmp_dir" ]]; then
    setup_tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/mac-setup.XXXXXXXX")"
  fi
}

step="Homebrew setup"
brew_bin="$(command -v brew || true)"
if [[ -z "$brew_bin" ]]; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$candidate" ]]; then
      brew_bin="$candidate"
      break
    fi
  done
fi
if [[ -z "$brew_bin" ]]; then
  make_temp_dir
  curl --fail --show-error --location --retry 3 --connect-timeout 15 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh \
    --output "$setup_tmp_dir/install-homebrew.sh"
  [[ -s "$setup_tmp_dir/install-homebrew.sh" ]] || die "The Homebrew installer download was empty."
  /bin/bash "$setup_tmp_dir/install-homebrew.sh"
  case "$(uname -m)" in
    arm64) brew_bin=/opt/homebrew/bin/brew ;;
    x86_64) brew_bin=/usr/local/bin/brew ;;
    *) die "Unsupported Mac architecture: $(uname -m)" ;;
  esac
  [[ -x "$brew_bin" ]] || die "Homebrew installation did not create $brew_bin."
fi
brew_environment="$("$brew_bin" shellenv)"
eval "$brew_environment"
brew_prefix="$("$brew_bin" --prefix)"

install_bundle() {
  local bundle_file="$1"
  if $upgrade_packages; then
    "$brew_bin" bundle install "--file=$bundle_file" --upgrade
  else
    "$brew_bin" bundle install "--file=$bundle_file" --no-upgrade
  fi
}

step="Homebrew packages"
install_bundle "$dotfiles_dir/Brewfile"
if ! $skip_apps; then
  install_bundle "$dotfiles_dir/Brewfile.apps"
fi

step="Neovim submodule checkout"
if ! git -C "$dotfiles_dir" submodule update --init --recursive; then
  die "Could not initialize submodules. Check GitHub SSH access for the repository in .gitmodules, then rerun."
fi
[[ -f "$dotfiles_dir/.config/nvim/init.lua" ]] || die "The Neovim submodule is missing init.lua."
for source_path in "${config_sources[@]}"; do
  [[ -e "$dotfiles_dir/$source_path" ]] || die "Missing configuration source: $source_path"
done

step="Node installation"
node_version="$(cat "$dotfiles_dir/.nvmrc")"
[[ -n "$node_version" ]] || die ".nvmrc must select a Node version."
if [[ -z "${NVM_DIR:-}" ]]; then
  if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
    export NVM_DIR="$XDG_CONFIG_HOME/nvm"
  else
    export NVM_DIR="$HOME/.nvm"
  fi
else
  export NVM_DIR
fi
mkdir -p "$NVM_DIR"
nvm_loader="$NVM_DIR/nvm.sh"
if [[ ! -s "$nvm_loader" ]]; then
  nvm_loader="$brew_prefix/opt/nvm/nvm.sh"
fi
[[ -s "$nvm_loader" ]] || die "Cannot find nvm.sh for the installed NVM."

# NVM is a shell function and does not support errexit. Keep its shell options
# local to this subprocess and check each operation explicitly.
install_node() (
  set +e
  set +u
  trap - ERR
  . "$nvm_loader" --no-use || exit $?
  nvm install "$node_version" || exit $?
  nvm exec "$node_version" node --version || exit $?
)
if ! install_node; then
  die "Node installation or verification failed."
fi

step="Python installation"
pyenv install --skip-existing "$python_version"
PYENV_VERSION="$python_version" pyenv exec python --version
if $set_python_default; then
  pyenv global "$python_version"
else
  log "Preserving the global Python selection; use --set-python-default to change it."
fi

step="configuration links"
for index in "${!config_sources[@]}"; do
  source_path="$dotfiles_dir/${config_sources[$index]}"
  target_path="${config_targets[$index]}"
  if [[ "$source_path" -ef "$target_path" ]]; then
    continue
  fi
  saved_path=""
  if [[ -e "$target_path" || -L "$target_path" ]]; then
    $backup_conflicts || die "Configuration changed during setup: $target_path. Rerun with --backup."
    if [[ -z "$backup_dir" ]]; then
      mkdir -p "$HOME/.dotfiles-backups"
      backup_dir="$(mktemp -d "$HOME/.dotfiles-backups/mac-setup.XXXXXXXX")"
    fi
    saved_path="$backup_dir/${config_sources[$index]}"
    mkdir -p "$(dirname "$saved_path")"
    mv -- "$target_path" "$saved_path"
    log "Backed up $target_path to $saved_path"
  fi
  mkdir -p "$(dirname "$target_path")"
  if ! ln -s -- "$source_path" "$target_path"; then
    if [[ -n "$saved_path" ]]; then
      mv -- "$saved_path" "$target_path"
    fi
    die "Could not link $target_path."
  fi
  log "Linked $target_path"
done

step="tmux plugins"
tpm_dir="$HOME/.tmux/plugins/tpm"
if [[ ! -e "$tpm_dir" && ! -L "$tpm_dir" ]]; then
  make_temp_dir
  git clone --depth 1 https://github.com/tmux-plugins/tpm "$setup_tmp_dir/tpm"
  mkdir -p "$(dirname "$tpm_dir")"
  mv -- "$setup_tmp_dir/tpm" "$tpm_dir"
fi
[[ -x "$tpm_dir/bin/install_plugins" ]] || die "Existing TPM directory is incomplete: $tpm_dir"
# TPM reads its plugin path from a tmux server. Use a sessionless private
# server so an existing user's server and its configuration are never changed.
make_temp_dir
tmux_socket="$setup_tmp_dir/tmux.sock"
if ! tmux -S "$tmux_socket" -f /dev/null start-server \; \
  set-option -s exit-empty off \; \
  set-environment -g TMUX_PLUGIN_MANAGER_PATH "$HOME/.tmux/plugins/"; then
  die "Could not start the isolated plugin installer. Check tmux, or rerun with --upgrade."
fi
TMUX="$tmux_socket,0,0" TMUX_PLUGIN_MANAGER_PATH="$HOME/.tmux/plugins/" "$tpm_dir/bin/install_plugins"

step="verification"
tmux -V
nvim --version
log "Mac setup complete. Open a new terminal to load the configuration."
if [[ -n "$backup_dir" ]]; then
  log "Previous configuration is preserved in $backup_dir"
fi
