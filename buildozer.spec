[app]

title = 自动打卡工具
package.name = auto_clock_in
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0

android.minapi = 21
android.api = 34
android.ndk = 27b

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
fullscreen = 0
orientation = portrait

requirements = python3,kivy==2.2.0,requests

log_level = 2
debug = 0

[buildozer]
log_level = 2
show_commands = 1
build_dir = ./.buildozer
bin_dir = ./.buildozer/bin
