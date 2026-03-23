[app]

# --- Identidade do aplicativo ---
title = RoadPy
package.name = roadpy
package.domain = br.ufrgs.igeo

# Arquivo principal
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Versão
version = 1.0.0

# Dependências Python
requirements = python3,kivy==2.3.0

# Orientação
orientation = portrait

# Android
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Ícone (substitua pelo ícone real em 512x512)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/splash.png

# Cor do presplash
android.presplash_color = #0D1117

# Fullscreen
fullscreen = 0

# Log
log_level = 2

[buildozer]
# Nível de log (0=erro, 1=info, 2=debug)
log_level = 2
warn_on_root = 1
