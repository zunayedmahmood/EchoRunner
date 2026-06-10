# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

block_cipher = None

# Detect platform for binary includes
binaries = []
if sys.platform.startswith("win"):
    # Check if we have OpenAL dll locally
    dll_path = Path("OpenAL32.dll")
    if dll_path.exists():
        binaries.append((str(dll_path), "."))
elif sys.platform.startswith("darwin"):
    dylib_path = Path("libopenal.dylib")
    if dylib_path.exists():
        binaries.append((str(dylib_path), "."))
else:
    so_path = Path("libopenal.so.1")
    if so_path.exists():
        binaries.append((str(so_path), "."))

datas = [
    ('config', 'config'),
    ('levels', 'levels'),
    ('assetLibrary', 'assetLibrary'),
    ('soundLibrary', 'soundLibrary'),
]

# Add readme files
if Path("README.md").exists():
    datas.append(("README.md", "."))
if Path("README_FIRST_RUN.txt").exists():
    datas.append(("README_FIRST_RUN.txt", "."))

a = Analysis(
    ['src/echorunner/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['platformdirs', 'yaml', 'pygame', 'wave', 'ctypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EchoRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # console=True is required for interactive consent and terminal post-session prompts
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
