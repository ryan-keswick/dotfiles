#!/usr/bin/env bash

echo "Setting up mac Ryan's way"

wget

# Install these
# https://alacritty.org/
# https://docs.docker.com/desktop/release-notes/

hdiutil attach Docker.dmg
/Volumes/Docker/Docker.app/Contents/MacOS/install
hdiutil detach /Volumes/Docker

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/ryankeswick/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

brew upgrade
brew install ansible \
  aspell \
  bash \
  btop \
  buildkite-agent \
  coreutils \
  docker \
  gh \
  git \
  git-lfs \
  gmp \
  gnu-sed \
  gnutls \
  go \
  htop \
  jq \
  marksman \
  moreutils \
  ncurses \
  neovim \
  nettle \
  nmap \
  nvm \
  nvtop \
  openssl@3 \
  p11-kit \
  poetry \
  postgresql@15 \
  pyenv \
  qemu \
  readline \
  redis \
  ripgrep \
  ruff \
  snappy \
  sqlite \
  starship \
  telnet \
  terraform \
  terraform-docs \
  tflint \
  tmux \
  tree \
  watch \
  wget \
  xz \
  zstd

brew install --cask slack \
  spotify \
  docker

echo "Installing Tmux configuration"
mkdir -p ~/.config/tmux
cp ~/src/ryan-keswick/dotfiles/.config/tmux/tmux.conf ~/.config/tmux/
echo "Installing TPM (Tmux Plugin Manager)"
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
echo "Installing Tmux plugins"
~/.tmux/plugins/tpm/bin/install_plugins

echo "Install NerdFond"
mkdir -p ~/Library/Fonts
curl -L "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.3.0/JetBrainsMono.zip" -o /tmp/jbm.zip
unzip -o /tmp/jbm.zip -d ~/Library/Fonts
rm /tmp/jbm.zip
echo "JetBrains Mono Nerd Font installed!"

echo "Installing Neovim config..."
cp -r "$HOME/dotfiles/.config/nvim" "$HOME/.config/"
