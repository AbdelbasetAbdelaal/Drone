import urllib.request
import json
import zipfile
import subprocess
import os

run_id = "30165493967"
url = f"https://api.github.com/repos/AbdelbasetAbdelaal/Drone/actions/runs/{run_id}/artifacts"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
res = json.loads(urllib.request.urlopen(req).read())
artifacts = res.get('artifacts', [])

print(f"Found {len(artifacts)} artifacts for Run #{run_id}:")
for a in artifacts:
    print(" - Name:", a['name'], "| Size:", a['size_in_bytes'], "| Download URL:", a['archive_download_url'])
