import urllib.request
import json
import zipfile
import os

url = "https://api.github.com/repos/AbdelbasetAbdelaal/Drone/actions/runs/30163983455/artifacts"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
res = json.loads(urllib.request.urlopen(req).read())
artifacts = res.get('artifacts', [])

if artifacts:
    download_url = artifacts[0]['archive_download_url']
    print(f"Artifact name: {artifacts[0]['name']}")
    print(f"Download URL: {download_url}")
