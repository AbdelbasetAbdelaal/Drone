import urllib.request
import json
import zipfile
import subprocess
import time
import os

print("Waiting for GitHub Actions build 30164981401 to complete...")
while True:
    try:
        req = urllib.request.Request("https://api.github.com/repos/AbdelbasetAbdelaal/Drone/actions/runs/30164981401", headers={'User-Agent': 'Mozilla/5.0'})
        res = json.loads(urllib.request.urlopen(req).read())
        status = res.get("status")
        conclusion = res.get("conclusion")
        print(f"Build status: {status} | Conclusion: {conclusion}")
        if status == "completed":
            if conclusion == "success":
                print("Build succeeded!")
            break
    except Exception as e:
        print(f"Error checking run: {e}")
    time.sleep(15)
