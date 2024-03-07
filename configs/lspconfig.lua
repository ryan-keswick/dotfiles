local base = require("plugins.configs.lspconfig")
local on_attach = base.on_attatch
local capabilities = base.capabilities

local lspconfig = require("lspconfig")

local servers = {
  "cssls",
  "eslint",
  "tailwindcss",
  "terraformls",
  "tsserver", 
}

for _, lsp in ipairs(servers) do
  lspconfig[lsp].setup {
     on_attach = on_attach,
     capabilities = capabilities,
  }
end

