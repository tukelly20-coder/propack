# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['client.py'],
    pathex=[],
    binaries=[],
    datas=[('language.txt', '.'), ('last_name.txt', '.'), ('last_employee.txt', '.'), ('last_ip.txt', '.'), ('last_category.txt', '.'), ('used_codes.json', '.'), ('Toolsysnc', 'Toolsysnc')],
    hiddenimports=['PySide6.QtNetwork', 'socket', 'select'],
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
    name='client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
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
    name='自动生成图纸编码- V7 散件图',
)
