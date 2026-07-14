# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['web_collector.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['sqlalchemy', 'pymysql', 'sqlalchemy.dialects.mysql.pymysql', 'sqlalchemy.dialects.postgresql', 'sqlalchemy.dialects.sqlite', 'sqlalchemy.dialects.mssql', 'flask', 'werkzeug', 'jinja2', 'pyodbc', 'oracledb'],
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
    name='zhixi_collector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
