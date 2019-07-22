# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[("./text.yml", "data"), ("./datafiles/dependencies.sh", "data/datafiles"),
             ("./datafiles/install.sh", "data/datafiles"),
             ("./datafiles/update_node_project.sh", "data/datafiles"),
             ("./datafiles/install_convoy.sh", "data/datafiles"),
             ("./datafiles/third_parties/dm_dev_partition.sh", "data/datafiles/third_parties"),
             ("./datafiles/convoy.service.j2", "data/datafiles"),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
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
          console=True )
