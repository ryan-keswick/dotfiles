if [[ "$(uname)" == "Darwin" ]]; then
  IS_MAC=true
else
  IS_MAC=false
fi

if $IS_MAC; then
  if command -v brew >/dev/null 2>&1; then
    eval "$(brew shellenv)"
  elif [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

typeset -U path PATH
export PATH="$HOME/.local/bin:$PATH"

if [[ -z "${NVM_DIR:-}" && -n "${XDG_CONFIG_HOME:-}" ]]; then
  NVM_DIR="$XDG_CONFIG_HOME/nvm"
fi
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -s "$NVM_DIR/nvm.sh" && -r "$NVM_DIR/nvm.sh" ]]; then
  source "$NVM_DIR/nvm.sh"
else
  if $IS_MAC; then
    if command -v brew >/dev/null 2>&1; then
      nvm_script="$(brew --prefix)/opt/nvm/nvm.sh"
      if [[ -s "$nvm_script" && -r "$nvm_script" ]]; then
        source "$nvm_script"
      fi
      unset nvm_script
    fi
  fi
fi

if $IS_MAC; then
  export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
  [[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  if command -v pyenv >/dev/null 2>&1; then
    eval "$(pyenv init - zsh)"
  fi

  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
fi

DOCKER_BUILDKIT=1
ZSH_THEME=""
if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi

if [[ -r "$HOME/.zshrc.local" ]]; then
  source "$HOME/.zshrc.local"
fi
