return {
  {
    "christoomey/vim-tmux-navigator",
    cmd = {
      "TmuxNavigateLeft",
      "TmuxNavigateDown",
      "TmuxNavigateUp",
      "TmuxNavigateRight",
      "TmuxNavigatePrevious",
    },
    keys = {
      { "<c-h>", "<cmd><C-U>TmuxNavigateLeft<cr>" },
      { "<c-j>", "<cmd><C-U>TmuxNavigateDown<cr>" },
      { "<c-k>", "<cmd><C-U>TmuxNavigateUp<cr>" },
      { "<c-l>", "<cmd><C-U>TmuxNavigateRight<cr>" },
      { "<c-\\>", "<cmd><C-U>TmuxNavigatePrevious<cr>" },
    },
  },

  {
    "neovim/nvim-lspconfig",
    config = function()
      require "configs.lspconfig"
    end,
  },

  {
  	"nvim-treesitter/nvim-treesitter",
  	opts = {
  		ensure_installed = {
  			"bash",
        "c",
        "cmake",
        "css",
        "dockerfile",
        "go",
        "gomod",
        "gowork",
        "hcl",
        "html",
        "http",
        "javascript",
        "json",
        "lua",
        "make",
        "markdown",
        "python",
        "regex",
        "ruby",
        "rust",
        "terraform",
        "tsx",
        "toml",
        "vim",
        "yaml",
        "zig",
  		},
  	},
  },
}
