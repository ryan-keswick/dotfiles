-- This file needs to have same structure as nvconfig.lua 
-- https://github.com/NvChad/ui/blob/v3.0/lua/nvconfig.lua
-- Please read that file to know all available options :( 

---@type ChadrcConfig
local M = {}

M.base46 = {
  theme = "mountain",

  changed_themes = {
    all = {
      base_30 = {
        white = "#ffffff",
        darker_black = "#000000",
        black = "#161616", --  nvim bg
        black2 = "#202020",
        one_bg = "#2a2a2a", -- real bg of onedark
        one_bg2 = "#343434",
        one_bg3 = "#3c3c3c",
        grey = "#464646",
        grey_fg = "#4c4c4c",
        grey_fg2 = "#555555",
        light_grey = "#5f5f5f",
        red = "#ee5396",
        baby_pink = "#ff7eb6",
        pink = "#be95ff",
        line = "#383747", -- for lines like vertsplit
        green = "#42be65",
        vibrant_green = "#08bdba",
        nord_blue = "#78a9ff",
        blue = "#33b1ff",
        yellow = "#FAE3B0",
        sun = "#ffe9b6",
        purple = "#d0a9e5",
        dark_purple = "#c7a0dc",
        teal = "#B5E8E0",
        orange = "#F8BD96",
        cyan = "#3ddbd9",
        statusline_bg = "#202020",
        lightbg = "#2a2a2a",
        pmenu_bg = "#3ddbd9",
        folder_bg = "#78a9ff",
        lavender = "#c7d1ff",
      },

      base_16 = {
        base00 = "#000000",
        base01 = "#161616",
        base02 = "#292929",
        base03 = "#424242",
        base04 = "#dde1e6",
        base05 = "#f2f4f8",
        base06 = "#ffffff",
        base07 = "#08bdba",
        base08 = "#3ddbd9",
        base09 = "#78a9ff",
        base0A = "#ee5396",
        base0B = "#33b1ff",
        base0C = "#ff7eb6",
        base0D = "#42be65",
        base0E = "#be95ff",
        base0F = "#82cfff",
      }
    }
  }
}

return M
