# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['nally_bridge', 'nally_bridge.cli', 'nally_bridge.bridge', 'nally_bridge.config', 'nally_bridge.executor', 'nally_bridge.security', 'nally_bridge.autostart', 'websockets', 'websockets.legacy', 'websockets.legacy.client', 'psutil', 'dotenv']
hiddenimports += collect_submodules('websockets')


a = Analysis(
    ['C:\\Users\\chuki\\Desktop\\NallyBridge\\nally_bridge\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\chuki\\Desktop\\NallyBridge\\.env.example', '.'), ('C:\\Users\\chuki\\Desktop\\NallyBridge\\README.md', '.')],
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
    name='NallyBridge',
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
    codesign_identity=None,
    entitlements_file=None,
)
