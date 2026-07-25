import urllib.request
import json
import zipfile
import subprocess
import os

url = "https://api.github.com/repos/AbdelbasetAbdelaal/Drone/actions/runs/30164981401/artifacts"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
res = json.loads(urllib.request.urlopen(req).read())
artifacts = res.get('artifacts', [])

if artifacts:
    download_url = artifacts[0]['archive_download_url']
    print(f"Downloading artifact from: {download_url}")
    zip_path = os.path.join(os.path.dirname(__file__), "DroneHunter-Android-APK.zip")
    extract_dir = os.path.join(os.path.dirname(__file__), "extracted_apk")
    os.makedirs(extract_dir, exist_ok=True)

    # Note: GitHub API artifact zip requires token if private, but for public repo:
    req_dl = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req_dl) as response, open(zip_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Downloaded zip successfully!")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("Extracted APK successfully!")
        
        apk_files = [f for f in os.listdir(extract_dir) if f.endswith('.apk')]
        if apk_files:
            apk_full_path = os.path.join(extract_dir, apk_files[0])
            print(f"APK file path: {apk_full_path}")
    except Exception as e:
        print(f"Direct download info: {e}")
