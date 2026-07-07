from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

from aiproject.config import external_config_dir
from aiproject.main import run
from aiproject.scraper import load_champion_pages_from_index_html, load_hextech_pages_from_index_html


HOST = "127.0.0.1"
PORT = 8765


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Poro</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fc;
      --panel: #eef2f7;
      --text: #111827;
      --muted: #5f6877;
      --line: #d8dee8;
      --button: #ffffff;
      --button-disabled: #d6dce6;
      --card: #ffffff;
      --field: #eef2f7;
      --hover: #e6ebf2;
      --shadow: rgba(0, 0, 0, 0.08);
      --modal-bg: #f8fafc;
      --hex-icon-bg: #111827;
    }

    * {
      box-sizing: border-box;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }

    *::-webkit-scrollbar {
      width: 0;
      height: 0;
      display: none;
    }

    html,
    body {
      overflow: hidden;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
      letter-spacing: 0;
    }

    body.dark {
      color-scheme: dark;
      --bg: #0f1012;
      --panel: #1b1d21;
      --text: #f3f3f3;
      --muted: #a2a7af;
      --line: #2a2e35;
      --button: #2a2d33;
      --button-disabled: #343840;
      --card: #17191d;
      --field: #191b20;
      --hover: #23262c;
      --shadow: rgba(0, 0, 0, 0.38);
      --modal-bg: #0f1012;
      --hex-icon-bg: #090b10;
    }

    .app {
      height: 100vh;
      min-height: 100vh;
      display: grid;
      grid-template-columns: 68px 1fr;
      grid-template-rows: 56px 1fr auto;
      transition: grid-template-columns 0.18s ease;
    }

    .app.nav-expanded {
      grid-template-columns: 206px 1fr;
    }

    .sidebar {
      grid-row: 1 / 4;
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      background: color-mix(in srgb, var(--panel) 82%, var(--bg));
      border-right: 1px solid var(--line);
      overflow: hidden;
      z-index: 60;
    }

    header {
      grid-column: 2;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      padding: 0 26px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 18px;
      font-weight: 500;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      position: relative;
      overflow: hidden;
      flex: 0 0 auto;
      background:
        radial-gradient(circle at 24px 8px, rgba(255, 255, 255, 0.9) 0 6px, transparent 7px),
        linear-gradient(135deg, #22135f 0%, #5033c8 42%, #00b9ff 72%, #0b123f 100%);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
    }

    .brand-icon::before,
    .brand-icon::after {
      content: "";
      position: absolute;
      top: 14px;
      width: 15px;
      height: 12px;
      border-radius: 55% 55% 45% 45%;
      background: #f6e8ff;
      transform: rotate(-24deg);
      box-shadow: inset 0 -2px 0 rgba(112, 45, 126, 0.35);
    }

    .brand-icon::before { left: 1px; }
    .brand-icon::after {
      right: 1px;
      transform: rotate(24deg);
    }

    .poro {
      position: absolute;
      left: 4px;
      right: 4px;
      bottom: 1px;
      height: 26px;
      border-radius: 48% 48% 42% 42%;
      background: #ffffff;
      box-shadow: 0 -4px 10px rgba(255, 255, 255, 0.45);
    }

    .poro::before,
    .poro::after {
      content: "";
      position: absolute;
      top: 8px;
      width: 5px;
      height: 7px;
      border-radius: 50%;
      background: #111111;
    }

    .poro::before { left: 10px; }
    .poro::after { right: 10px; }

    .poro-gem {
      position: absolute;
      top: 2px;
      left: 15px;
      width: 12px;
      height: 12px;
      border-radius: 3px;
      background: linear-gradient(135deg, #d9b5ff, #7d35d7);
      transform: rotate(45deg);
      box-shadow: 0 0 8px rgba(201, 137, 255, 0.95);
      z-index: 2;
    }

    .poro-tongue {
      position: absolute;
      left: 17px;
      bottom: -2px;
      width: 10px;
      height: 12px;
      border-radius: 7px 7px 8px 8px;
      background: #e95a83;
      z-index: 3;
    }

    .sidebar-back,
    .sidebar-toggle,
    .side-tab,
    .settings-trigger,
    .theme-trigger {
      width: calc(100% - 8px);
      height: 48px;
      border: 0;
      background: transparent;
      color: var(--muted);
      font-size: 18px;
      line-height: 1;
      padding: 0;
      margin: 4px;
      border-radius: 8px;
      cursor: pointer;
      display: grid;
      grid-template-columns: 56px 1fr;
      align-items: center;
      text-align: left;
    }

    .sidebar-back {
      height: 54px;
      margin-top: 8px;
      color: var(--text);
      font-size: 24px;
    }

    .sidebar-toggle {
      color: var(--text);
      font-size: 23px;
    }

    .side-nav {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 6px 0;
    }

    .side-bottom {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 8px 0 14px;
    }

    .nav-icon {
      width: 56px;
      text-align: center;
      font-size: 18px;
      font-weight: 650;
    }

    .nav-icon svg {
      width: 22px;
      height: 22px;
      stroke: currentColor;
      stroke-width: 1.9;
      stroke-linecap: round;
      stroke-linejoin: round;
      fill: none;
      vertical-align: middle;
    }

    .nav-label {
      min-width: 0;
      overflow: hidden;
      white-space: nowrap;
      font-size: 14px;
      font-weight: 600;
    }

    .app:not(.nav-expanded) .nav-label {
      opacity: 0;
    }

    .sidebar-back:hover,
    .sidebar-toggle:hover,
    .side-tab:hover,
    .settings-trigger:hover,
    .theme-trigger:hover {
      background: var(--hover);
      color: var(--text);
    }

    .side-tab.active,
    .settings-trigger.active {
      background: var(--hover);
      color: var(--text);
      border-radius: 8px;
    }

    .side-tab.active .nav-icon,
    .settings-trigger.active .nav-icon {
      color: #246b76;
    }

    body.dark .side-tab.active .nav-icon,
    body.dark .settings-trigger.active .nav-icon {
      color: #7dd8e8;
    }

    .settings-view {
      flex-direction: column;
      overflow: auto;
      padding: 8px 4px 40px;
    }

    .settings-page-title {
      margin: 0 0 18px;
      font-size: 28px;
      font-weight: 650;
    }

    .settings-panel,
    .about-panel {
      width: 100%;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 26px var(--shadow);
      padding: 22px;
    }

    .settings-title {
      margin: 0 0 14px;
      font-size: 16px;
      font-weight: 600;
    }

    .setting-field {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }

    .setting-label {
      color: var(--text);
      font-size: 13px;
      font-weight: 600;
    }

    .api-key-input {
      width: 100%;
      height: 44px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--card);
      color: var(--text);
      font: 14px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
    }

    .api-key-input:focus {
      border-color: var(--text);
      outline: none;
    }

    .save-settings {
      width: 100%;
      height: 42px;
      margin-top: 14px;
      border-radius: 12px;
      background: var(--text);
      color: var(--bg);
      font-size: 14px;
      cursor: pointer;
    }

    .settings-note {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    .about-panel {
      margin-top: 18px;
      display: grid;
      grid-template-columns: 30px 1fr auto;
      align-items: center;
      gap: 14px;
    }

    .about-icon {
      color: var(--text);
      font-size: 22px;
      text-align: center;
    }

    .about-title {
      font-size: 17px;
      font-weight: 650;
    }

    .about-copy {
      margin-top: 4px;
      color: var(--muted);
      font-size: 14px;
    }

    .github-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #0097a7;
      text-decoration: none;
      font-size: 16px;
      font-weight: 650;
      white-space: nowrap;
    }

    .github-link:hover {
      text-decoration: underline;
    }

    main {
      grid-column: 2;
      display: flex;
      align-items: stretch;
      justify-content: center;
      padding: 36px 48px 8px;
      min-height: 0;
    }

    .workspace {
      width: min(1180px, 100%);
      display: grid;
      grid-template-rows: 1fr;
      gap: 18px;
      min-height: 0;
    }

    .view {
      display: none;
      min-height: 0;
    }

    .view.active {
      display: flex;
      min-height: 0;
    }

    .conversation {
      width: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 0;
    }

    .empty { margin: auto; }

    .messages {
      display: none;
      flex-direction: column;
      gap: 18px;
      overflow: auto;
      padding: 16px 10px 24px;
      min-height: 0;
      height: 100%;
    }

    .message {
      width: min(880px, 100%);
      line-height: 1.8;
      font-size: 16px;
      white-space: pre-wrap;
    }

    .message.user {
      align-self: flex-end;
      width: auto;
      max-width: min(760px, 90%);
      background: var(--panel);
      border-radius: 22px;
      padding: 12px 18px;
    }

    .message.assistant {
      align-self: flex-start;
      padding: 4px 2px;
    }

    .roster-view,
    .hextech-view {
      flex-direction: column;
      overflow: hidden;
    }

    .roster-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 2px 4px 14px;
    }

    .roster-title {
      margin: 0;
      font-size: 22px;
      font-weight: 650;
    }

    .roster-count {
      color: var(--muted);
      font-size: 13px;
    }

    .catalog-search {
      width: 100%;
      margin: 0 0 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--field);
      padding: 0 16px;
    }

    .catalog-search span {
      color: var(--muted);
      font-size: 18px;
    }

    .catalog-search input {
      width: 100%;
      height: 48px;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--text);
      font: 15px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
    }

    .champion-grid,
    .hextech-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(108px, 1fr));
      gap: 14px;
      overflow: auto;
      padding: 2px 4px 24px;
    }

    .hextech-grid {
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    }

    .champion-card,
    .hextech-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--card);
      color: var(--text);
      padding: 10px;
      height: auto;
      cursor: pointer;
      text-align: center;
      font: inherit;
      transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    .champion-card:hover,
    .hextech-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 28px var(--shadow);
    }

    .champion-card img,
    .hextech-card img {
      width: 72px;
      height: 72px;
      border-radius: 16px;
      object-fit: cover;
      display: block;
      margin: 0 auto 8px;
      background: var(--panel);
    }

    .hextech-card {
      display: grid;
      grid-template-columns: 58px 1fr;
      gap: 10px;
      text-align: left;
      align-items: center;
      min-height: 92px;
    }

    .hextech-card img {
      width: 54px;
      height: 54px;
      border-radius: 12px;
      margin: 0;
      background: var(--hex-icon-bg);
    }

    .champion-name,
    .hextech-name {
      font-size: 14px;
      font-weight: 650;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .champion-title,
    .hextech-tier {
      margin-top: 2px;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .hextech-tier {
      color: var(--text);
      font-weight: 600;
    }

    .champion-modal {
      position: fixed;
      inset: 0 0 0 68px;
      z-index: 40;
      display: none;
      grid-template-rows: auto 1fr;
      background: var(--modal-bg);
      color: var(--text);
    }

    body.nav-expanded .champion-modal {
      left: 206px;
    }

    .champion-modal.open {
      display: grid;
    }

    .modal-bar {
      height: 64px;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 0 24px;
      border-bottom: 1px solid var(--line);
    }

    .back-button {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: var(--hover);
      color: var(--text);
      font-size: 24px;
      cursor: pointer;
    }

    .modal-title {
      font-size: 18px;
      font-weight: 650;
    }

    .modal-body {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 32px;
      padding: 36px 48px;
      min-height: 0;
    }

    .modal-hero {
      align-self: start;
      text-align: center;
    }

    .modal-hero img {
      width: 180px;
      height: 180px;
      border-radius: 32px;
      object-fit: cover;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.14);
    }

    .modal-hero img.hextech-icon {
      background: var(--hex-icon-bg);
      padding: 16px;
    }

    .modal-name {
      margin: 18px 0 4px;
      font-size: 28px;
      font-weight: 700;
    }

    .modal-subtitle {
      color: var(--muted);
      font-size: 15px;
    }

    .modal-answer {
      overflow: auto;
      white-space: pre-wrap;
      line-height: 1.85;
      font-size: 16px;
      padding: 4px 4px 48px;
    }

    .modal-answer.detail-panel {
      align-self: start;
      max-height: calc(100vh - 136px);
      padding: 22px 24px;
      border-radius: 18px;
      background: var(--panel);
      color: var(--text);
      border: 1px solid var(--line);
      box-shadow: 0 18px 44px var(--shadow);
    }

    .hextech-term {
      display: inline;
      border-bottom: 1px dotted currentColor;
      color: #3346b8;
      cursor: help;
      font-weight: 650;
    }

    body.dark .hextech-term {
      color: #9da5ff;
    }

    .hextech-tooltip {
      position: fixed;
      z-index: 80;
      width: min(360px, calc(100vw - 24px));
      pointer-events: none;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--card);
      color: var(--text);
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
      padding: 14px;
    }

    .hextech-tooltip[hidden] {
      display: none;
    }

    .tooltip-head {
      display: grid;
      grid-template-columns: 48px 1fr;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }

    .tooltip-head img {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: var(--hex-icon-bg);
    }

    .tooltip-name {
      font-size: 15px;
      font-weight: 700;
    }

    .tooltip-tier,
    .tooltip-desc {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .tooltip-desc {
      color: var(--text);
    }

    .composer-wrap {
      grid-column: 2;
      padding: 8px 48px 48px;
      display: flex;
      justify-content: center;
    }

    .composer {
      width: min(1092px, 100%);
      min-height: 146px;
      background: var(--panel);
      border-radius: 34px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 14px;
      padding: 24px 16px 12px 30px;
    }

    textarea {
      resize: none;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--text);
      font: 25px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
      line-height: 1.4;
      min-width: 0;
      height: 76px;
      padding: 0;
    }

    textarea::placeholder { color: var(--muted); opacity: 1; }

    .controls {
      align-self: end;
      display: flex;
      align-items: center;
      gap: 10px;
      padding-bottom: 0;
    }

    button,
    select {
      border: 0;
      outline: 0;
      height: 56px;
      background: var(--button);
      color: var(--text);
      font: 24px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
    }

    select {
      appearance: none;
      border-radius: 28px;
      padding: 0 48px 0 22px;
      background-image:
        linear-gradient(45deg, transparent 50%, #666 50%),
        linear-gradient(135deg, #666 50%, transparent 50%);
      background-position:
        calc(100% - 24px) 26px,
        calc(100% - 17px) 26px;
      background-size: 7px 7px;
      background-repeat: no-repeat;
      font-size: 24px;
    }

    .send {
      width: 56px;
      border-radius: 50%;
      background: var(--button-disabled);
      color: var(--bg);
      cursor: pointer;
    }

    .send.ready {
      background: var(--text);
    }

    .send:disabled {
      cursor: wait;
      opacity: 0.55;
    }

    @media (max-width: 760px) {
      .app.nav-expanded {
        grid-template-columns: 168px 1fr;
      }
      body.nav-expanded .champion-modal {
        left: 168px;
      }
      main { padding: 18px 18px 4px; }
      .composer-wrap { padding: 8px 16px 22px; }
      .composer {
        grid-template-columns: 1fr;
        min-height: 180px;
        padding: 22px;
      }
      textarea { font-size: 20px; }
      .controls { justify-content: flex-end; }
      select { max-width: 160px; font-size: 19px; }
      .modal-body {
        grid-template-columns: 1fr;
        padding: 22px;
      }
      .modal-hero img {
        width: 128px;
        height: 128px;
        border-radius: 24px;
      }
      .about-panel {
        grid-template-columns: 30px 1fr;
      }
      .github-link {
        grid-column: 2;
        justify-self: start;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar" aria-label="主导航">
      <button class="sidebar-back" id="globalBackButton" type="button" title="返回" aria-label="返回">
        <span class="nav-icon">←</span>
        <span class="nav-label">返回</span>
      </button>
      <button class="sidebar-toggle" id="sidebarToggle" type="button" title="展开导航" aria-label="展开导航">
        <span class="nav-icon">☰</span>
        <span class="nav-label">菜单</span>
      </button>
      <nav class="side-nav" aria-label="主页栏目">
        <button class="side-tab active" id="aiTab" type="button" title="AI回答">
          <span class="nav-icon">⌂</span>
          <span class="nav-label">AI回答</span>
        </button>
        <button class="side-tab" id="rosterTab" type="button" title="英雄名录">
          <span class="nav-icon">👤︎</span>
          <span class="nav-label">英雄名录</span>
        </button>
        <button class="side-tab" id="hextechTab" type="button" title="海克斯强化">
          <span class="nav-icon">👻︎</span>
          <span class="nav-label">海克斯强化</span>
        </button>
      </nav>
      <div class="side-bottom">
        <button class="theme-trigger" id="themeButton" type="button" title="夜间模式" aria-label="夜间模式">
          <span class="nav-icon" id="themeIcon">☾</span>
          <span class="nav-label" id="themeLabel">夜间模式</span>
        </button>
        <button class="settings-trigger" id="settingsButton" type="button" title="设置" aria-label="设置">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"></path>
              <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2.1 2.1 0 0 1-2.96 2.96l-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.55V21a2.1 2.1 0 0 1-4.2 0v-.08A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06a2.1 2.1 0 0 1-2.96-2.96l.06-.06a1.7 1.7 0 0 0 .34-1.88 1.7 1.7 0 0 0-1.55-1.03H2.5a2.1 2.1 0 0 1 0-4.2h.08A1.7 1.7 0 0 0 4.1 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06A2.1 2.1 0 1 1 6.66 3.7l.06.06A1.7 1.7 0 0 0 8.6 4.1a1.7 1.7 0 0 0 1.03-1.55V2.5a2.1 2.1 0 0 1 4.2 0v.08A1.7 1.7 0 0 0 15 4.1a1.7 1.7 0 0 0 1.88-.34l.06-.06a2.1 2.1 0 1 1 2.96 2.96l-.06.06A1.7 1.7 0 0 0 19.4 8.6a1.7 1.7 0 0 0 1.55 1.03H21a2.1 2.1 0 0 1 0 4.2h-.08A1.7 1.7 0 0 0 19.4 15Z"></path>
            </svg>
          </span>
          <span class="nav-label">设置</span>
        </button>
      </div>
    </aside>

    <header>
      <div class="brand">
        <span class="brand-icon" aria-hidden="true">
          <span class="poro-gem"></span>
          <span class="poro"><span class="poro-tongue"></span></span>
        </span>
        <span>Poro</span>
      </div>
    </header>

    <main>
      <section class="workspace">
        <section class="view active" id="aiView">
          <section class="conversation">
            <div class="empty" id="empty"></div>
            <div class="messages" id="messages"></div>
          </section>
        </section>

        <section class="view roster-view" id="rosterView">
          <div class="roster-head">
            <h1 class="roster-title">英雄名录</h1>
            <span class="roster-count" id="rosterCount">加载中</span>
          </div>
          <label class="catalog-search">
            <span>⌕</span>
            <input id="championSearch" type="search" placeholder="搜索英雄中文名、称号或 ID" autocomplete="off" />
          </label>
          <div class="champion-grid" id="championGrid"></div>
        </section>

        <section class="view hextech-view" id="hextechView">
          <div class="roster-head">
            <h1 class="roster-title">海克斯强化</h1>
            <span class="roster-count" id="hextechCount">加载中</span>
          </div>
          <label class="catalog-search">
            <span>⌕</span>
            <input id="hextechSearch" type="search" placeholder="搜索海克斯中文名、评级或描述" autocomplete="off" />
          </label>
          <div class="hextech-grid" id="hextechGrid"></div>
        </section>

        <section class="view settings-view" id="settingsView">
          <h1 class="settings-page-title">设置</h1>
          <section class="settings-panel" aria-labelledby="settingsTitle">
            <h2 class="settings-title" id="settingsTitle">DeepSeek API Key</h2>
            <label class="setting-field">
              <span class="setting-label">API Key</span>
              <input class="api-key-input" id="apiKeyInput" type="password" placeholder="sk-..." autocomplete="off" />
            </label>
            <button class="save-settings" id="saveSettings" type="button">保存 API Key</button>
            <p class="settings-note" id="settingsNote">API Key 会保存到 exe 同目录或项目根目录的 .env 文件。</p>
          </section>
          <section class="about-panel" aria-label="关于">
            <div class="about-icon">ⓘ</div>
            <div>
              <div class="about-title">关于</div>
              <div class="about-copy">版权所有 © 2026, qianxunql. 当前版本 1.0.0</div>
            </div>
            <a class="github-link" href="https://github.com/qianxunql/Hextech" target="_blank" rel="noreferrer">GitHub qianxunql/Hextech</a>
          </section>
        </section>
      </section>
    </main>

    <section class="composer-wrap">
      <form class="composer" id="form">
        <textarea id="question" placeholder="Send a message" autocomplete="off"></textarea>
        <div class="controls">
          <button class="send" id="send" type="submit" title="发送">↑</button>
        </div>
      </form>
    </section>

    <section class="champion-modal" id="championModal" aria-hidden="true">
      <div class="modal-bar">
        <button class="back-button" id="modalBack" type="button" aria-label="返回">←</button>
        <div class="modal-title" id="modalTitle">英雄详情</div>
      </div>
      <div class="modal-body">
        <aside class="modal-hero">
          <img id="modalImage" alt="" />
          <div class="modal-name" id="modalName"></div>
          <div class="modal-subtitle" id="modalSubtitle"></div>
        </aside>
        <article class="modal-answer" id="modalAnswer">正在生成推荐...</article>
      </div>
    </section>

    <div class="hextech-tooltip" id="hextechTooltip" hidden></div>
  </div>

  <script>
    const form = document.querySelector("#form");
    const app = document.querySelector(".app");
    const input = document.querySelector("#question");
    const send = document.querySelector("#send");
    const empty = document.querySelector("#empty");
    const messages = document.querySelector("#messages");
    const globalBackButton = document.querySelector("#globalBackButton");
    const sidebarToggle = document.querySelector("#sidebarToggle");
    const settingsButton = document.querySelector("#settingsButton");
    const themeButton = document.querySelector("#themeButton");
    const themeIcon = document.querySelector("#themeIcon");
    const themeLabel = document.querySelector("#themeLabel");
    const apiKeyInput = document.querySelector("#apiKeyInput");
    const saveSettings = document.querySelector("#saveSettings");
    const settingsNote = document.querySelector("#settingsNote");
    const aiTab = document.querySelector("#aiTab");
    const rosterTab = document.querySelector("#rosterTab");
    const hextechTab = document.querySelector("#hextechTab");
    const aiView = document.querySelector("#aiView");
    const rosterView = document.querySelector("#rosterView");
    const hextechView = document.querySelector("#hextechView");
    const settingsView = document.querySelector("#settingsView");
    const composerWrap = document.querySelector(".composer-wrap");
    const championGrid = document.querySelector("#championGrid");
    const rosterCount = document.querySelector("#rosterCount");
    const championSearch = document.querySelector("#championSearch");
    const hextechGrid = document.querySelector("#hextechGrid");
    const hextechCount = document.querySelector("#hextechCount");
    const hextechSearch = document.querySelector("#hextechSearch");
    const championModal = document.querySelector("#championModal");
    const modalBack = document.querySelector("#modalBack");
    const modalTitle = document.querySelector("#modalTitle");
    const modalImage = document.querySelector("#modalImage");
    const modalName = document.querySelector("#modalName");
    const modalSubtitle = document.querySelector("#modalSubtitle");
    const modalAnswer = document.querySelector("#modalAnswer");
    const hextechTooltip = document.querySelector("#hextechTooltip");

    let championItems = [];
    let hextechItems = [];
    let modalRequestId = 0;
    let activeTooltipHextechId = "";
    let activeViewName = "ai";
    let previousViewName = "ai";

    function applyTheme(theme) {
      const isDark = theme === "dark";
      document.body.classList.toggle("dark", isDark);
      themeIcon.textContent = isDark ? "☀" : "☾";
      themeLabel.textContent = isDark ? "日间模式" : "夜间模式";
      themeButton.title = isDark ? "日间模式" : "夜间模式";
      themeButton.setAttribute("aria-label", themeButton.title);
      localStorage.setItem("hextech:theme", isDark ? "dark" : "light");
    }

    function applyNavExpanded(expanded) {
      app.classList.toggle("nav-expanded", expanded);
      document.body.classList.toggle("nav-expanded", expanded);
      sidebarToggle.title = expanded ? "收起导航" : "展开导航";
      sidebarToggle.setAttribute("aria-label", sidebarToggle.title);
      localStorage.setItem("hextech:navExpanded", expanded ? "1" : "0");
    }

    async function loadSettings() {
      try {
        const response = await fetch("/api/settings");
        const data = await response.json();
        apiKeyInput.value = "";
        apiKeyInput.placeholder = data.hasDeepseekApiKey ? "已保存，输入新 Key 可覆盖" : "sk-...";
      } catch {
        settingsNote.textContent = "读取设置失败。";
      }
    }

    async function saveApiKey() {
      saveSettings.disabled = true;
      settingsNote.textContent = "正在保存...";
      try {
        const response = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ deepseekApiKey: apiKeyInput.value.trim() }),
        });
        const data = await response.json();
        settingsNote.textContent = data.ok ? "已保存到 .env。" : "保存失败。";
      } catch (error) {
        settingsNote.textContent = `保存失败：${error}`;
      } finally {
        saveSettings.disabled = false;
      }
    }

    function setReady() {
      send.classList.toggle("ready", input.value.trim().length > 0);
    }

    function showMessages() {
      empty.style.display = "none";
      messages.style.display = "flex";
    }

    function addMessage(role, text) {
      showMessages();
      const node = document.createElement("div");
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
      return node;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function escapeRegExp(value) {
      const slash = String.fromCharCode(92);
      const specials = new Set([slash, ".", "*", "+", "?", "^", "$", "{", "}", "(", ")", "|", "[", "]"]);
      return Array.from(String(value))
        .map((char) => specials.has(char) ? slash + char : char)
        .join("");
    }

    async function ensureHextechItems() {
      if (hextechItems.length) return hextechItems;
      const response = await fetch("/api/hextech");
      const data = await response.json();
      hextechItems = data.hextech || [];
      return hextechItems;
    }

    function linkifyHextechTerms(text) {
      const newline = String.fromCharCode(10);
      if (!hextechItems.length) {
        return escapeHtml(text).replaceAll(newline, "<br>");
      }
      const byName = new Map();
      hextechItems.forEach((item) => {
        if (item.name && item.name.length >= 2) {
          byName.set(item.name, item);
        }
      });
      const names = Array.from(byName.keys()).sort((a, b) => b.length - a.length);
      if (!names.length) {
        return escapeHtml(text).replaceAll(newline, "<br>");
      }
      const pattern = new RegExp(names.map(escapeRegExp).join("|"), "g");
      return escapeHtml(text)
        .replace(pattern, (match) => {
          const item = byName.get(match);
          if (!item) return match;
          return `<span class="hextech-term" data-hextech-id="${escapeHtml(item.id)}">${match}</span>`;
        })
        .replaceAll(newline, "<br>");
    }

    async function setModalAnswerWithHextechTerms(text) {
      try {
        await ensureHextechItems();
        modalAnswer.innerHTML = linkifyHextechTerms(text);
      } catch {
        modalAnswer.textContent = text;
      }
    }

    async function setMessageWithHextechTerms(node, text) {
      try {
        await ensureHextechItems();
        node.innerHTML = linkifyHextechTerms(text);
      } catch {
        node.textContent = text;
      }
    }

    function setActiveView(view, options = {}) {
      if (championModal.classList.contains("open")) {
        closeChampionModal();
      }
      const isRoster = view === "roster";
      const isHextech = view === "hextech";
      const isAi = view === "ai";
      const isSettings = view === "settings";
      if (view !== activeViewName && !options.skipHistory) {
        previousViewName = activeViewName;
      }
      activeViewName = view;
      aiTab.classList.toggle("active", isAi);
      rosterTab.classList.toggle("active", isRoster);
      hextechTab.classList.toggle("active", isHextech);
      settingsButton.classList.toggle("active", isSettings);
      aiView.classList.toggle("active", isAi);
      rosterView.classList.toggle("active", isRoster);
      hextechView.classList.toggle("active", isHextech);
      settingsView.classList.toggle("active", isSettings);
      composerWrap.style.display = isAi ? "flex" : "none";
      if (isRoster && !championGrid.dataset.loaded) {
        loadChampions();
      }
      if (isHextech && !hextechGrid.dataset.loaded) {
        loadHextechs();
      }
      if (isSettings) {
        loadSettings();
      }
    }

    function goBack() {
      if (championModal.classList.contains("open")) {
        closeChampionModal();
        return;
      }
      if (activeViewName === "settings") {
        setActiveView(previousViewName || "ai", { skipHistory: true });
        return;
      }
      if (activeViewName !== "ai") {
        setActiveView("ai");
        return;
      }
      input.focus();
    }

    async function loadChampions() {
      rosterCount.textContent = "加载中";
      try {
        const response = await fetch("/api/champions");
        const data = await response.json();
        championItems = data.champions || [];
        renderChampions();
      } catch (error) {
        rosterCount.textContent = "加载失败";
        championGrid.textContent = `加载英雄名录失败：${error}`;
      }
    }

    function renderChampions() {
      championGrid.dataset.loaded = "true";
      const keyword = championSearch.value.trim().toLowerCase();
      const champions = championItems.filter((champion) => {
        const haystack = `${champion.name} ${champion.title || ""} ${champion.id}`.toLowerCase();
        return haystack.includes(keyword);
      });
      rosterCount.textContent = `${champions.length} / ${championItems.length} 位英雄`;
      championGrid.textContent = "";
      champions.forEach((champion) => {
        const card = document.createElement("button");
        card.className = "champion-card";
        card.type = "button";
        card.innerHTML = `
          <img src="${champion.image}" alt="${champion.name}" loading="lazy" />
          <div class="champion-name">${champion.name}</div>
          <div class="champion-title">${champion.title || champion.id}</div>
        `;
        card.addEventListener("click", () => openChampionModal(champion));
        championGrid.appendChild(card);
      });
    }

    async function loadHextechs() {
      hextechCount.textContent = "加载中";
      try {
        await ensureHextechItems();
        renderHextechs();
      } catch (error) {
        hextechCount.textContent = "加载失败";
        hextechGrid.textContent = `加载海克斯强化失败：${error}`;
      }
    }

    function renderHextechs() {
      hextechGrid.dataset.loaded = "true";
      const keyword = hextechSearch.value.trim().toLowerCase();
      const hextechs = hextechItems.filter((item) => {
        const haystack = `${item.name} ${item.tier} ${item.description} ${item.id}`.toLowerCase();
        return haystack.includes(keyword);
      });
      hextechCount.textContent = `${hextechs.length} / ${hextechItems.length} 条强化`;
      hextechGrid.textContent = "";
      hextechs.forEach((item) => {
        const card = document.createElement("button");
        card.className = "hextech-card";
        card.type = "button";
        card.dataset.hextechId = item.id;
        card.innerHTML = `
          <img src="${item.image}" alt="${item.name}" loading="lazy" />
          <div>
            <div class="hextech-name">${item.name}</div>
            <div class="hextech-tier">${item.tier}</div>
          </div>
        `;
        card.addEventListener("click", () => openHextechModal(item));
        hextechGrid.appendChild(card);
      });
    }

    async function openChampionModal(champion) {
      const requestId = ++modalRequestId;
      championModal.classList.add("open");
      championModal.setAttribute("aria-hidden", "false");
      modalAnswer.classList.remove("detail-panel");
      modalTitle.textContent = "海克斯推荐";
      modalImage.src = champion.image;
      modalImage.alt = champion.name;
      modalImage.classList.remove("hextech-icon");
      modalName.textContent = champion.name;
      modalSubtitle.textContent = champion.title || champion.id;
      modalAnswer.textContent = "正在生成推荐...";

      const question = `${champion.name}适合什么海克斯强化？请给出简洁实战推荐。`;
      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        if (requestId !== modalRequestId) return;
        await setModalAnswerWithHextechTerms(data.answer || "没有得到回答。");
      } catch (error) {
        if (requestId !== modalRequestId) return;
        modalAnswer.textContent = `出错了：${error}`;
      }
    }

    function closeChampionModal() {
      modalRequestId += 1;
      championModal.classList.remove("open");
      championModal.setAttribute("aria-hidden", "true");
      modalAnswer.classList.remove("detail-panel");
      modalAnswer.textContent = "";
      hideHextechTooltip();
    }

    async function openHextechModal(item) {
      const requestId = ++modalRequestId;
      championModal.classList.add("open");
      championModal.setAttribute("aria-hidden", "false");
      modalAnswer.classList.remove("detail-panel");
      modalTitle.textContent = "海克斯详情";
      modalImage.src = item.image;
      modalImage.alt = item.name;
      modalImage.classList.add("hextech-icon");
      modalName.textContent = item.name;
      modalSubtitle.textContent = item.tier;
      modalAnswer.textContent = "正在检索知识库并生成解析...";

      const question = `海克斯强化「${item.name}」（${item.tier}）适合哪些英雄或玩法？请基于知识库给出简洁实战解析：适合谁、怎么拿收益最高、哪些情况要避开。`;
      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        if (requestId !== modalRequestId) return;
        await setModalAnswerWithHextechTerms(data.answer || "没有得到回答。");
      } catch (error) {
        if (requestId !== modalRequestId) return;
        modalAnswer.textContent = `出错了：${error}`;
      }
    }

    function positionHextechTooltip(event) {
      if (hextechTooltip.hidden) return;
      const gap = 14;
      const rect = hextechTooltip.getBoundingClientRect();
      const left = Math.min(event.clientX + gap, window.innerWidth - rect.width - 12);
      const top = Math.min(event.clientY + gap, window.innerHeight - rect.height - 12);
      hextechTooltip.style.left = `${Math.max(12, left)}px`;
      hextechTooltip.style.top = `${Math.max(12, top)}px`;
    }

    function showHextechTooltip(term, event) {
      const item = hextechItems.find((hextech) => hextech.id === term.dataset.hextechId);
      if (!item) return;
      if (activeTooltipHextechId !== item.id) {
        activeTooltipHextechId = item.id;
        hextechTooltip.innerHTML = `
          <div class="tooltip-head">
            <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}" />
            <div>
              <div class="tooltip-name">${escapeHtml(item.name)}</div>
              <div class="tooltip-tier">${escapeHtml(item.tier)}</div>
            </div>
          </div>
          <div class="tooltip-desc">${escapeHtml(item.description || "暂无描述")}</div>
        `;
      }
      hextechTooltip.hidden = false;
      positionHextechTooltip(event);
    }

    function hideHextechTooltip() {
      activeTooltipHextechId = "";
      hextechTooltip.hidden = true;
    }

    input.addEventListener("input", setReady);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!question || send.disabled) return;

      input.value = "";
      setReady();
      addMessage("user", question);
      const pending = addMessage("assistant", "正在检索知识库并思考...");
      send.disabled = true;

      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        await setMessageWithHextechTerms(pending, data.answer || "没有得到回答。");
      } catch (error) {
        pending.textContent = `出错了：${error}`;
      } finally {
        send.disabled = false;
        input.focus();
      }
    });

    settingsButton.addEventListener("click", () => setActiveView("settings"));

    themeButton.addEventListener("click", () => {
      applyTheme(document.body.classList.contains("dark") ? "light" : "dark");
    });

    sidebarToggle.addEventListener("click", () => {
      applyNavExpanded(!app.classList.contains("nav-expanded"));
    });

    globalBackButton.addEventListener("click", goBack);
    saveSettings.addEventListener("click", saveApiKey);
    aiTab.addEventListener("click", () => setActiveView("ai"));
    rosterTab.addEventListener("click", () => setActiveView("roster"));
    hextechTab.addEventListener("click", () => setActiveView("hextech"));
    championSearch.addEventListener("input", renderChampions);
    hextechSearch.addEventListener("input", renderHextechs);
    modalBack.addEventListener("click", closeChampionModal);
    document.addEventListener("mouseover", (event) => {
      const term = event.target.closest?.(".hextech-term, .hextech-card");
      if (term) showHextechTooltip(term, event);
    });
    document.addEventListener("mousemove", (event) => {
      if (event.target.closest?.(".hextech-term, .hextech-card")) {
        positionHextechTooltip(event);
      }
    });
    document.addEventListener("mouseout", (event) => {
      const term = event.target.closest?.(".hextech-term, .hextech-card");
      if (term && !term.contains(event.relatedTarget)) {
        hideHextechTooltip();
      }
    });

    applyTheme(localStorage.getItem("hextech:theme") || "light");
    applyNavExpanded(localStorage.getItem("hextech:navExpanded") === "1");
    input.focus();
    setReady();
  </script>
</body>
</html>
"""


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        if (bundle_dir / "data").exists():
            return bundle_dir
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def model_overrides() -> dict[str, str]:
    return {"model_provider": "deepseek"}


def champion_catalog() -> list[dict[str, str]]:
    try:
        pages = load_champion_pages_from_index_html("data/html/champions_index.html")
    except RuntimeError:
        return []

    champions: list[dict[str, str]] = []
    image_root = Path("英雄名录 _ ARAM Hextech Wiki_files")
    for page in pages:
        fields: dict[str, str] = {}
        for line in page.text.splitlines():
            if "：" in line:
                key, value = line.split("：", 1)
                fields[key.strip()] = value.strip()

        image_path = image_root / f"{page.name}.webp"
        champions.append(
            {
                "id": page.name,
                "name": fields.get("英雄名称", page.name),
                "title": fields.get("中文称号", ""),
                "rating": fields.get("目录评级", "-"),
                "image": f"/assets/champions/{page.name}.webp" if image_path.exists() else "",
            }
        )

    return sorted(champions, key=lambda item: item["name"])


def hextech_catalog() -> list[dict[str, str]]:
    try:
        pages = load_hextech_pages_from_index_html("海克斯强化列表 _ ARAM Hextech Wiki.html")
    except RuntimeError:
        return []

    image_root = Path("海克斯强化列表 _ ARAM Hextech Wiki_files")
    tier_order = {"棱彩阶": 0, "黄金阶": 1, "白银阶": 2}
    hextechs: list[dict[str, str]] = []
    for page in pages:
        image_path = image_root / f"{page.hextech_id}.webp"
        hextechs.append(
            {
                "id": page.hextech_id,
                "name": page.name,
                "tier": page.tier,
                "ratingRank": str(tier_order.get(page.tier, 99)),
                "description": page.description,
                "image": f"/assets/hextech/{page.hextech_id}.webp" if image_path.exists() else "",
            }
        )

    return sorted(hextechs, key=lambda item: (int(item["ratingRank"]), item["name"]))


def env_file_path(path: str = ".env") -> Path:
    return external_config_dir() / path


def read_env_value(key: str, path: str = ".env") -> str:
    env_path = env_file_path(path)
    if not env_path.exists():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        env_key, value = line.split("=", 1)
        if env_key.strip() == key:
            return value.strip().strip('"').strip("'")
    return ""


def write_env_value(key: str, value: str, path: str = ".env") -> None:
    env_path = env_file_path(path)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines() if env_path.exists() else []
    updated = False
    next_lines: list[str] = []
    for raw_line in lines:
        if raw_line.strip().startswith("#") or "=" not in raw_line:
            next_lines.append(raw_line)
            continue
        env_key, _ = raw_line.split("=", 1)
        if env_key.strip() == key:
            next_lines.append(f"{key}={value}")
            updated = True
        else:
            next_lines.append(raw_line)
    if not updated:
        next_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")
    os.environ[key] = value


class HextechRequestHandler(BaseHTTPRequestHandler):
    server_version = "PoroWeb/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_text(HTML, "text/html; charset=utf-8")
            return
        if path == "/api/champions":
            self._send_json({"champions": champion_catalog()})
            return
        if path == "/api/hextech":
            self._send_json({"hextech": hextech_catalog()})
            return
        if path == "/health":
            self._send_json({"ok": True})
            return
        if path == "/api/settings":
            self._send_json({"hasDeepseekApiKey": bool(read_env_value("DEEPSEEK_API_KEY"))})
            return
        if path.startswith("/assets/champions/"):
            self._send_champion_image(path)
            return
        if path.startswith("/assets/hextech/"):
            self._send_hextech_image(path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/settings":
            self._handle_settings_post()
            return

        if path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("question is required")
            answer = run(question, overrides=model_overrides())
            self._send_json({"answer": answer})
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"error": str(exc), "answer": f"出错了：{exc}"}, status=500)

    def _handle_settings_post(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            api_key = str(payload.get("deepseekApiKey", "")).strip()
            write_env_value("DEEPSEEK_API_KEY", api_key)
            self._send_json({"ok": True})
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_text(self, content: str, content_type: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_champion_image(self, path: str) -> None:
        filename = Path(unquote(path)).name
        if not filename.endswith(".webp") or "/" in filename or "\\" in filename:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        image_path = Path("英雄名录 _ ARAM Hextech Wiki_files") / filename
        if not image_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = image_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "image/webp")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_hextech_image(self, path: str) -> None:
        filename = Path(unquote(path)).name
        if not filename.endswith(".webp") or "/" in filename or "\\" in filename:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        image_path = Path("海克斯强化列表 _ ARAM Hextech Wiki_files") / filename
        if not image_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = image_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "image/webp")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = HOST, port: int = PORT) -> None:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")
    server = ThreadingHTTPServer((host, port), HextechRequestHandler)
    print(f"Poro web UI: http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
