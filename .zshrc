if [[ "$(uname)" == "Darwin" ]]; then
  IS_MAC=true
else
  IS_MAC=false
fi

if $IS_MAC; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

if $IS_MAC; then
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init - zsh)"

  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
fi

eval "$(starship init zsh)"
