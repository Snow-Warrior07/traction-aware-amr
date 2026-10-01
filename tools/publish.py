"""Create a dedicated repository and push only this project's files."""
import subprocess
from pathlib import Path
from github_api import request
root=Path(__file__).resolve().parents[1]
def git(*args,output=False):
    command=["git","-c","safe.directory="+root.as_posix(),*args]
    if output:return subprocess.check_output(command,cwd=root,text=True).strip()
    return subprocess.run(command,cwd=root,check=True)
user=request("/user")["login"]
if user!="Snow-Warrior07":raise RuntimeError("Signed-in account differs from the verified project account")
try:
    existing=request("/repos/"+user+"/traction-aware-amr")
except RuntimeError as error:
    if "HTTP 404" not in str(error):raise
    existing=request("/user/repos","POST",{"name":"traction-aware-amr","private":False,
        "description":"Virtual warehouse rover: linear/nonlinear control, traction, ROS 2, PCB and live tests."})
if not (root/".git").exists():
    if existing.get("size",0)>0:raise RuntimeError("Remote repository is not empty; inspect it before integrating")
    git("init","-b",existing.get("default_branch","main"))
remotes=git("remote",output=True).splitlines()
if "origin" not in remotes:git("remote","add","origin",existing["clone_url"])
elif git("remote","get-url","origin",output=True)!=existing["clone_url"]:raise RuntimeError("Unexpected origin URL")
git("add",".")
dirty=git("diff","--cached","--name-only",output=True)
if dirty:
    git("commit","-m","Implement phased rover simulation, controllers, virtual PCB and verification")
git("push","-u","origin","HEAD")
print(existing["html_url"])
