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
  ripgrep \
  docker \
  git \ 
  terraform \
  jq \
  neovim
