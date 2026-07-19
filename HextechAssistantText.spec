# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


python_dlls = Path(sys.base_prefix) / "DLLs"
ssl_binaries = [
    (str(python_dlls / "libssl-3-x64.dll"), "."),
    (str(python_dlls / "libcrypto-3-x64.dll"), "."),
]


datas = [
    ("data", "data"),
    ("英雄名录 _ ARAM Hextech Wiki.html", "."),
    ("英雄名录 _ ARAM Hextech Wiki_files", "英雄名录 _ ARAM Hextech Wiki_files"),
    ("海克斯强化列表 _ ARAM Hextech Wiki.html", "."),
    ("海克斯强化列表 _ ARAM Hextech Wiki_files", "海克斯强化列表 _ ARAM Hextech Wiki_files"),
    ("src\\aiproject\\static", "aiproject\\static"),
    ("assets\\poro.ico", "assets"),
    (".env.example", "."),
] + collect_data_files("rapidocr_onnxruntime")

hiddenimports = (
    [
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
    ]
    + collect_submodules("PIL")
    + collect_submodules("mss")
    + collect_submodules("rapidfuzz")
    + collect_submodules("rapidocr_onnxruntime")
    + collect_submodules("onnxruntime")
)

a = Analysis(
    ["src\\aiproject\\desktop_text.py"],
    pathex=["src"],
    binaries=ssl_binaries,
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
    [],
    exclude_binaries=True,
    name="Poro-TextIndex",
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Poro-TextIndex",
)
