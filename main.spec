# -*- mode: python -*-

# import distutils
# if distutils.distutils_path.endswith('__init__.py'):
#    distutils.distutils_path = os.path.dirname(distutils.distutils_path)

block_cipher = None

a = Analysis(
    ['node_cli/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
       ("./text.yml", "data"),
       ("./datafiles/configure-iptables.sh", "data/datafiles"),
       ("./datafiles/backup-install.sh", "data/datafiles"),
       ("./datafiles/helper.sh", "data/datafiles")
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True
)
