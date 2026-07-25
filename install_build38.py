import urllib.request
import json
import zipfile
import os
import shutil
import subprocess

run_id = "30167942308"
target_apk_dir = r"D:\AI_Projects\drone_hunter\Drone_Hunter_Game_Package"
target_apk_path = os.path.join(target_apk_dir, "dronehuntermobile-1.0.0-arm64-v8a-debug.apk")

os.makedirs(target_apk_dir, exist_ok=True)

print(f"Fetching artifacts list for run {run_id}...")
url = f"https://api.github.com/repos/AbdelbasetAbdelaal/Drone/actions/runs/{run_id}/artifacts"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
res = json.loads(urllib.request.urlopen(req).read())

artifacts = res.get('artifacts', [])
if not artifacts:
    print("No artifacts found!")
    sys.exit(1)

download_url = artifacts[0]['archive_download_url']
print(f"Downloading artifact from {download_url}...")

zip_path = os.path.join(target_apk_dir, "artifact.zip")

# Note: github API download needs auth token if private, or direct redirect.
# Let's check download via curl or python urllib:
token = os.environ.get("GITHUB_TOKEN", "")
headers = {'User-Agent': 'Mozilla/5.0'}
if token:
    headers['Authorization'] = f'token {token}'

req = urllib.request.Request(download_url, headers=headers)
with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_file:
    shutil.copyfileobj(resp, out_file)

print(f"Downloaded zip to {zip_path}. Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(target_apk_dir)

print(f"Extracted contents into {target_apk_dir}")

# Look for .apk file in target_apk_dir
for f in os.listdir(target_apk_dir):
    if f.endswith(".apk") and f != "dronehuntermobile-1.0.0-arm64-v8a-debug.apk":
        src_path = os.path.join(target_apk_dir, f)
        shutil.move(src_path, target_apk_path)
        print(f"Renamed {f} -> dronehuntermobile-1.0.0-arm64-v8a-debug.apk")
        break

print(f"APK Ready at: {target_apk_path}")
