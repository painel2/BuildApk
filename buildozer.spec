[app]

title = Legendas YT
package.name = legendasyt
package.domain = org.meuapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0.0

# Dependências essenciais para rodar o Python + Kivy + Legenda no Android
requirements = python3,kivy,youtube-transcript-api,requests,urllib3,certifi,idna,charset_normalizer,defusedxml

orientation = portrait
fullscreen = 0

# Permissão obrigatória para buscar a legenda na internet
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk_path = 
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
