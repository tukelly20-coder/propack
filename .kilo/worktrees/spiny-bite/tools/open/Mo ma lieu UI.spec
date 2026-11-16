# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Mở mã liệu UI.py'],
    pathex=[],
    binaries=[],
    datas=[('Mở mã liệu 打开链接VP.py', '.'), ('updater.py', '.'), ('version.json', '.'), ('favicon.ico', '.')],
    hiddenimports=[
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtNetwork', 'PySide6.QtXml',
        'openpyxl', 'openpyxl.cell', 'openpyxl.styles', 'openpyxl.utils',
        'requests', 'requests.api', 'requests.packages',
        'pandas', 'pandas.core',
        'pyperclip', 'pyperclip.clipboard',
        'numpy', 'numpy.core', 'numpy.lib',
        'logging', 'logging.handlers',
        'shutil', 'zipfile', 'subprocess',
    ],
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
    name='Mo ma lieu UI',
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
    icon='favicon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Mo ma lieu UI',
    icon='favicon.ico',
)
