#!/usr/bin/env bash

echo "Setting up mac Ryan's way"

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew upgrade

brew install \
  awscli \
  aws-vault \
  bash \
  btop \
  coreutils \
  docker \
  git \
  jq \
  postgresql \
  pyenv \
  moreutils \
  neovim \
  nvm \
  qemu \
  ripgrep \
  starship \
  terraform \
  tmux \
  wget

brew install --cask docker
brew install --cask slack
