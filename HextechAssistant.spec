# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


datas = [
    ("data", "data"),
    ("英雄名录 _ ARAM Hextech Wiki.html", "."),
    ("英雄名录 _ ARAM Hextech Wiki_files", "英雄名录 _ ARAM Hextech Wiki_files"),
    ("海克斯强化列表 _ ARAM Hextech Wiki.html", "."),
    ("海克斯强化列表 _ ARAM Hextech Wiki_files", "海克斯强化列表 _ ARAM Hextech Wiki_files"),
    ("src\\aiproject\\static", "aiproject\\static"),
    ("assets\\poro.ico", "assets"),
    (".env.example", "."),
]

hiddenimports = (
    collect_submodules("webview")
    + collect_submodules("chromadb")
    + collect_submodules("posthog")
)

a = Analysis(
    ["src\\aiproject\\desktop.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Poro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon="assets\\poro.ico",
    codesign_identity=None,
    entitlements_file=None,
)
