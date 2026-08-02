[app]

# (str) Title of your application
title = Legendas YT

# (str) Package name
package.name = legendasyt

# (str) Package domain (needed for android/ios packaging)
package.domain = org.meuapp

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# Comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,youtube-transcript-api,requests,urllib3,certifi,idna,charset_normalizer,defusedxml

# Adicione as novas bibliotecas necessárias para a Twitch e FFmpeg
requirements = python3,kivy,ffmpeg-python,streamlink


# (str) Supported orientations (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API required. 21 = Android 5.0
android.minapi = 21

# (str) Android NDK version to use (25b é a mais estável para o GitHub Actions)
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk manager
android.skip_update = False

# (bool) If True, automatically accept all SDK licenses
android.accept_sdk_license = True

# (str) The Android arch to build for
android.archs = arm64-v8a

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
