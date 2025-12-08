import os
import subprocess
import sys

print("🚀 Iniciando proyecto INEGI...")

# ===============================
# 1. BUSCAR RECOLECCION.PY
# ===============================
nombre_recoleccion = "recoleccion.py"
ruta_recoleccion = None

for root, dirs, files in os.walk("."):
    if nombre_recoleccion in files:
        ruta_recoleccion = os.path.join(root, nombre_recoleccion)
        break

if ruta_recoleccion:
    print(f"📥 Ejecutando: {ruta_recoleccion}")
    subprocess.run([sys.executable, ruta_recoleccion])
    print("✅ Recolección finalizada")
else:
    print("❌ No se encontró recoleccion.py")
    sys.exit()

# ===============================
# 2. BUSCAR DASHBOARD
# ===============================
nombre_dashboard = "dashboard_inegi.py"
ruta_dashboard = None

for root, dirs, files in os.walk("."):
    if nombre_dashboard in files:
        ruta_dashboard = os.path.join(root, nombre_dashboard)
        break

if ruta_dashboard:
    print(f"📊 Lanzando dashboard: {ruta_dashboard}")
    subprocess.run(["streamlit", "run", ruta_dashboard])
else:
    print("❌ No se encontró el archivo del dashboard")
