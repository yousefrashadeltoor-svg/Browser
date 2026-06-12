# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for JO Browser
# Usage: pyinstaller build.spec
#
# One-liner alternative:
#   pyinstaller --onefile --windowed --icon=assets/icons/jo.ico main.py
#
# For best results on Windows, install PyInstaller 6.x:
#   pip install pyinstaller

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets',  'assets'),
        ('ui',      'ui'),
        ('browser', 'browser'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngine',
        'PyQt6.QtPrintSupport',
        'cryptography',
        'aiohttp',
        'requests',
        'sqlite3',
        'json',
        'pathlib',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
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
    name='JOBrowser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window (GUI only)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/jo.ico',   # Replace with your .ico file
)
