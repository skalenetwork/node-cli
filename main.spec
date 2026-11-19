a = Analysis(
    ['node_cli/main.py'],
    pathex=[SPECPATH],
    datas=[
        ('text.yml', 'data'),
        ('datafiles/skaled-ssl-test', 'data/datafiles'),
    ],
)

pyz = PYZ(a.pure)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, name='main')
