# AGENTS.md

## Repository Overview

Personal dotfiles repo (`ryan-keswick/dotfiles`). This is consumed as a submodule by the parent `canvanauts/ryan-keswick-dotfiles` repo and stow'd into `~`.

## Contents

| File | Purpose |
|------|---------|
| `.zshrc` | Zsh config with `IS_MAC` platform guard |
| `.vimrc` | Vim configuration |
| `.tflint.hcl` | TFLint rules |
| `mac_setup.sh` | macOS bootstrap (Homebrew, apps) |
| `.config/` | XDG config (tmux, nvim submodule) |

## Submodules

### `.config/nvim` — `git@github.com:ryan-keswick/nvim.git`

Neovim configuration. Tracked as a nested submodule.

## Communication

Never mention Claude, Claude Code, Anthropic, or any AI assistant or AI tool in commit messages, code comments, or any files.

## Platform Guard

`.zshrc` uses an `IS_MAC` variable to conditionally run macOS-only commands (brew, pyenv, OBJC fork safety). All platform-specific code must be wrapped in `if $IS_MAC; then ... fi`.

## Committing

This repo is a submodule of `canvanauts/ryan-keswick-dotfiles`. After pushing here, update the submodule pointer in the parent repo.
