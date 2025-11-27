import os
import sys
import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Lista todos los CSV de una carpeta
def listar_csvs(carpeta: str):
    # Revisa que la carpeta exista
    p = Path(carpeta)
    if not p.exists() or not p.is_dir():
        print(f"[ERROR] Carpeta no encontrada: {carpeta}")
        return []
    # Regresa solo archivos .csv ordenados
    return sorted([f for f in p.iterdir() if f.suffix.lower() == ".csv"])


# Carga CSVs básicos a un dict {nombre: DataFrame}
def cargar_csvs_basico(carpeta: str):
    # No limpia nada raro, solo toma primera columna como Fecha y segunda como Valor
    resultados = {}
    for path in listar_csvs(carpeta):
        try:
            df = pd.read_csv(path)
            if df.shape[1] < 2:
                print(f"[WARN] {path.name} tiene menos de 2 columnas, se omite.")
                continue

            cols = df.columns.tolist()
            df2 = df[[cols[0], cols[1]]].copy()
            df2.columns = ["Fecha", "Valor"]

            # Intenta convertir Fecha a datetime pero sin forzar
            df2["Fecha"] = pd.to_datetime(df2["Fecha"], errors="ignore")
            resultados[path.stem] = df2

        except Exception as e:
            print(f"[WARN] No se pudo leer {path.name}: {e}")
    return resultados


# Grafica uno o varios DataFrames del dict
def graficar_basico(dfs_dict, nombres=None, guardar=False, carpeta_plots="plots"):
    # Si no hay datos, no hace nada
    if not dfs_dict:
        print("[INFO] No hay datos para graficar.")
        return None

    # Si no mandas nombres, grafica todos
    to_plot = nombres if nombres else list(dfs_dict.keys())
    to_plot = [n for n in to_plot if n in dfs_dict]

    if not to_plot:
        print("[WARN] No se encontraron nombres solicitados en los datos.")
        return None

    plt.figure(figsize=(10, 6))

    for nombre in to_plot:
        df = dfs_dict[nombre]
        x = df["Fecha"]
        y = pd.to_numeric(df["Valor"], errors="coerce")
        plt.plot(x, y, marker="o", label=nombre)

    plt.legend()
    plt.grid(True)
    plt.xlabel("Fecha")
    plt.ylabel("Valor")
    plt.title("Series de tiempo (modo local)")
    plt.tight_layout()

    if guardar:
        # Crea carpeta de plots si no existe
        os.makedirs(carpeta_plots, exist_ok=True)
        safe_name = "_".join(to_plot).replace(" ", "_")
        ruta = os.path.join(carpeta_plots, f"series_{safe_name}.png")
        plt.savefig(ruta, dpi=150)
        plt.close()
        print(f"[INFO] Gráfica guardada en: {ruta}")
        return ruta
    else:
        # Muestra la gráfica en pantalla
        plt.show()
        return None


# Punto de entrada principal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Modo local: cargar CSVs ya generados y graficar (sin API)."
    )
    parser.add_argument(
        "--carpeta",
        "-c",
        default="api_inegi",
        help="Carpeta donde buscar CSVs (por defecto: api_inegi)."
    )
    parser.add_argument(
        "--indicadores",
        "-i",
        nargs="*",
        default=None,
        help="Nombres de archivos (sin .csv) a graficar. Si no se especifica, se grafican todos."
    )
    parser.add_argument(
        "--guardar",
        "-g",
        action="store_true",
        help="Si se usa, guarda la gráfica en PNG en vez de solo mostrarla."
    )
    parser.add_argument(
        "--plots",
        "-p",
        default="plots",
        help="Carpeta donde guardar las imágenes si usas --guardar."
    )

    args = parser.parse_args()

    print(f"[INFO] Modo local activado. Buscando CSVs en: {args.carpeta}")
    dfs = cargar_csvs_basico(args.carpeta)

    if not dfs:
        print("[INFO] No se encontraron CSVs válidos. Saliendo.")
        sys.exit(0)

    print(f"[INFO] Series cargadas: {list(dfs.keys())}")
    graficar_basico(
        dfs,
        nombres=args.indicadores,
        guardar=args.guardar,
        carpeta_plots=args.plots
    )

    # Termina el script
    sys.exit(0)
