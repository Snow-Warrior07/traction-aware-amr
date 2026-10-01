"""Package the verified virtual project and website assets; no publication."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
README='''# Traction-aware AMR: editable KiCad 10 project

Open traction_carrier.kicad_pro in KiCad 10, then use the schematic and PCB buttons.
Open PCB Editor > View > 3D Viewer for the component model.

The project includes its custom AMR symbol library and project library tables.
Standard footprints/3D models use the installed KiCad 10 standard libraries.
Footprints are embedded in the PCB; schematic symbols are embedded and supplied
in AMR.kicad_sym. Schematic symbol UUIDs are linked to PCB footprints.

Carrier: 96 x 96 mm, two copper layers, 29 components, 29 connected signal/power
nets plus 18 single-pad no-connect nets. Motor current stays in external drivers.
No physical hardware is required for this demonstration.

Local KiCad 10.0.6 validation: ERC 0; all-track DRC 0; unconnected items 0;
schematic/PCB parity issues 0. Check reports are included under verification/.
Exports include two actual 3D renders, schematic SVG, board STEP, Gerbers/drill,
netlist and BOM. These software checks do not establish manufacturing readiness.

Demo: https://snow-warrior07.github.io/traction-aware-amr/
Source: https://github.com/Snow-Warrior07/traction-aware-amr
'''

def package(project_only=False):
    drc=json.loads((ROOT/'results/drc.json').read_text())
    erc=json.loads((ROOT/'results/erc.json').read_text())
    assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'], 'PCB check incomplete'
    assert not any(s['violations'] for s in erc['sheets']), 'ERC check incomplete'
    project=ROOT/'output/kicad/TractionAwareAMR-KiCad'
    project.mkdir(parents=True,exist_ok=True)
    for name in ['traction_carrier.kicad_pro','traction_carrier.kicad_sch','traction_carrier.kicad_pcb','AMR.kicad_sym','sym-lib-table','fp-lib-table','bom.csv']:
        shutil.copy2(ROOT/'hardware/kicad'/name,project/name)
    (project/'README.md').write_text(README,encoding='utf-8')
    for name in ['erc.json','drc.json','spice.json']:
        (project/'verification').mkdir(exist_ok=True);shutil.copy2(ROOT/'results'/name,project/'verification'/name)
    (project/'exports').mkdir(exist_ok=True)
    for name in ['carrier-top.png','carrier-isometric.png','carrier.step','traction_carrier.svg','carrier.net']:
        shutil.copy2(ROOT/'hardware/exports'/name,project/'exports'/name)
    downloads=SITE/'downloads';assets=SITE/'assets'
    downloads.mkdir(exist_ok=True);assets.mkdir(exist_ok=True)
    with zipfile.ZipFile(downloads/'traction-aware-amr-kicad.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in project.rglob('*'):
            if path.is_file():z.write(path,path.relative_to(project.parent))
        for path in (ROOT/'hardware/exports/gerbers').glob('*'):
            if path.is_file() and path.suffix in ['.gtl','.gbl','.gto','.gbo','.gts','.gbs','.gtp','.gbp','.gm1','.drl','.gbrjob']:
                z.write(path,Path(project.name)/'exports/gerbers'/path.name)
    with zipfile.ZipFile(downloads/'traction-aware-amr-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in (ROOT/'hardware/exports/gerbers').glob('*'):
            if path.is_file() and path.suffix in ['.gtl','.gbl','.gto','.gbo','.gts','.gbs','.gtp','.gbp','.gm1','.drl','.gbrjob']:z.write(path,path.name)
    if project_only:
        print(json.dumps({'project':str(project)}));return
    copies={'hardware/exports/carrier-top.png':'assets/carrier-top.png','hardware/exports/carrier-isometric.png':'assets/carrier-isometric.png','hardware/exports/traction_carrier.svg':'assets/schematic.svg','output/video/poster.png':'assets/demo-poster.png','output/video/traction-aware-amr-demo.mp4':'assets/traction-aware-amr-demo.mp4','output/video/transcript.md':'downloads/demo-transcript.md','output/pdf/traction-aware-amr-report.pdf':'downloads/phase-report.pdf','output/pdf/evidence.json':'downloads/evidence.json'}
    for src,dest in copies.items():shutil.copy2(ROOT/src,SITE/dest)
    srt=(ROOT/'output/video/traction-aware-amr-demo.srt').read_text(encoding='utf-8')
    (assets/'captions.vtt').write_text('WEBVTT\n\n'+re.sub(r'(\d\d:\d\d:\d\d),(\d\d\d)',r'\1.\2',srt),encoding='utf-8')
    (SITE/'.nojekyll').touch()
    print(json.dumps({'project':str(project),'website_assets':len(list(SITE.rglob('*'))),'kicad_zip_bytes':(downloads/'traction-aware-amr-kicad.zip').stat().st_size}))

def desktop():
    import os
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
        desktop=Path(os.path.expandvars(winreg.QueryValueEx(key,'Desktop')[0])).resolve()
    target=(desktop/'TractionAwareAMR-KiCad').resolve()
    assert target.parent==desktop
    source=ROOT/'output/kicad/TractionAwareAMR-KiCad'
    assert source.is_dir()
    target.mkdir(exist_ok=True)
    files=[]
    for path in source.rglob('*'):
        if not path.is_file():continue
        dest=target/path.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=path.read_bytes():raise RuntimeError('Desktop target already has different content: '+str(dest))
        shutil.copy2(path,dest)
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
        files.append({'file':str(path.relative_to(source)),'sha256':digest})
    # Copy the named Gerbers/drill without touching other Desktop files.
    for path in (ROOT/'hardware/exports/gerbers').glob('*'):
        if path.suffix not in ['.gtl','.gbl','.gto','.gbo','.gts','.gbs','.gtp','.gbp','.gm1','.drl','.gbrjob']:continue
        dest=target/'exports/gerbers'/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    receipt={'desktop_project':str(target/'traction_carrier.kicad_pro'),'copied_files':files}
    (ROOT/'output/desktop-delivery.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps({'desktop_project':receipt['desktop_project'],'verified_files':len(files)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--desktop',action='store_true');parser.add_argument('--project-only',action='store_true');args=parser.parse_args()
    desktop() if args.desktop else package(args.project_only)
