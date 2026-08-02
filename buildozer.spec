[app]

# (str) Title of your application
title = Twitch Clip App

# (str) Package name
package.name = twitchclipapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.meuapp

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (list) Include patterns (Inclui o executável do ffmpeg da pasta bin)
source.include_patterns = bin/*

# (str) Application versioning
version = 1.0.0

# (list) Application requirements (ffpyplayer e cython necessários pro Player de Vídeo)
requirements = python3,kivy,ffpyplayer,requests,urllib3,certifi,idna,charset_normalizer,streamlink

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version
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

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
