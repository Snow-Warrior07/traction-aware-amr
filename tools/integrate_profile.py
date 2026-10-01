"""Publish the prepared project link to the verified user's GitHub profile."""
import base64
import hashlib
import json
from pathlib import Path
from github_api import request

ROOT=Path(__file__).resolve().parents[1]
OWNER='Snow-Warrior07';BASE=f'/repos/{OWNER}/{OWNER}'
assert request('/user')['login']==OWNER
prepared=(ROOT/'docs/profile-project.md').read_bytes()
try:
    current=request(BASE+'/contents/README.md')
except RuntimeError as error:
    if 'HTTP 404' not in str(error):raise
    current=None
if current:
    content=base64.b64decode(current['content'])
    # Preserve any README that appeared since the read-only inspection.
    if b'<!-- traction-aware-amr:start -->' in content:
        before,rest=content.split(b'<!-- traction-aware-amr:start -->',1)
        _,after=rest.split(b'<!-- traction-aware-amr:end -->',1)
        prepared=before+b'<!-- traction-aware-amr:start -->\n'+prepared+b'\n<!-- traction-aware-amr:end -->'+after
    elif b'https://snow-warrior07.github.io/traction-aware-amr/' not in content:
        prepared=content+b'\n\n<!-- traction-aware-amr:start -->\n'+prepared+b'\n<!-- traction-aware-amr:end -->\n'
    else:prepared=content
payload={'message':'Feature traction-aware AMR demo and editable KiCad project','content':base64.b64encode(prepared).decode()}
if current:payload['sha']=current['sha']
if not current or base64.b64decode(current['content'])!=prepared:
    result=request(BASE+'/contents/README.md','PUT',payload)
else:result={'content':current}
request(f'/repos/{OWNER}/traction-aware-amr','PATCH',{'homepage':'https://snow-warrior07.github.io/traction-aware-amr/','description':'Virtual warehouse rover: linear/nonlinear control, traction, ROS 2, verified KiCad PCB and interactive measured demo.'})
request(f'/repos/{OWNER}/traction-aware-amr/topics','PUT',{'names':['control-engineering','ros2','kicad','digital-twin','lqr','nonlinear-control','robotics','simulation','traction-control']})
verified=request(BASE+'/contents/README.md')
assert base64.b64decode(verified['content'])==prepared
receipt={'profile_url':f'https://github.com/{OWNER}','profile_readme_url':verified['html_url'],'profile_content_sha256':hashlib.sha256(prepared).hexdigest(),'demo_url':'https://snow-warrior07.github.io/traction-aware-amr/'}
(ROOT/'output/profile-integration.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
