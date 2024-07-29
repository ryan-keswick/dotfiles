#!/usr/bin/env bash

echo "Setting up mac Ryan's way"

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/ryankeswick/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

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
brew install --cask spotify

git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
