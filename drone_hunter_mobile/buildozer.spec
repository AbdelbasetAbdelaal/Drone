[app]

# (str) Title of your application
title = Drone Hunter 2D Mobile

# (str) Package name
package.name = dronehuntermobile

# (str) Package domain (needed for android/ios packaging)
package.domain = com.antigravity.dronehunter

# (str) Source code where main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (list) Source files to exclude
source.exclude_patterns = license, .git, .buildozer, *.pyc, *.pyo, docs/*, tests/*

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = hostpython3==3.10.12,python3==3.10.12,pygame

# (str) Supported orientation
orientation = landscape

# (bool) Indicate if application should be fullscreen
fullscreen = 1

# (list) Permissions
permissions = INTERNET,RECORD_AUDIO

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) Automatically accept SDK license agreements
android.accept_sdk_licenses = True

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) Architecture targets
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
