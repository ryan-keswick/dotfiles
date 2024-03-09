local plugins = {
  {
    "christoomey/vim-tmux-navigator",
    lazy = false,
  },
  {
    "nvimtools/none-ls.nvim",
    event = "VeryLazy",
    opts = function()
      return require "custom.configs.null-ls"
    end,
  },
  {
    "neovim/nvim-lspconfig",
    config = function ()
      require "plugins.configs.lspconfig"
      require "custom.configs.lspconfig"
    end,
  },
  {
    "williamboman/mason.nvim",
    opts = {
      ensure_installed = {
        "black",
        "eslint-lsp",
        "mypy",
        "prettierd",
        "pyright",
        "ruff",
        "tailwindcss-language-server",
        "terraform-ls",
        "typescript-language-server",
      }
    }
  },
  {
    "windwp/nvim-ts-autotag",
    ft = {
      "javascript",
      "javascriptcreact",
      "typescript",
      "typescriptreact",
    },
    config = function()
      require("nvim-ts-autotag").setup()
    end
  },
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function()
      opts = require "plugins.configs.treesitter"
      opts.ensure_installed = {
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
      }
      return opts
    end
  },
}
return plugins
