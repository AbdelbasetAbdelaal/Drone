[app]

# (str) Title of your application
title = Drone Hunter 2D

# (str) Package name
package.name = dronehunter

# (str) Package domain (needed for android/ios packaging)
package.domain = com.antigravity.dronehunter

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3,pygame-ce

# (str) Extra arguments to pass to python-for-android to force ARM C cross-compilation
p4a.extra_args = --no-binary pygame-ce

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
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

# (list) List of inclusions using pattern matching
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning)
warn_on_root = 1
