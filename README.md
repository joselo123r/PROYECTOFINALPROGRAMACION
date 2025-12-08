Esto es un proyecto elaborado por alumnos de la Universidad Autonoma de Baja California, para la materia de programacion para la extraccion de datos.
El motivo de este proyecto es utilizar las distintas funciones y herramientas de python para extraer datos utilizando webscraping o exptrayendolo desde una api, asi mismo nuestra intencion es hacer limpieza y darle estructura a los datos para generar un dashboard de analisis final

📊 Proyecto INEGI – Extracción y Visualización de Datos

Este proyecto automatiza el proceso de recolección de datos, procesamiento y visualización mediante un flujo continuo usando Python y Streamlit.

📁 Estructura del Proyecto
PROYECTOFINALPROGRAMACION/
│
├── main.py                # Archivo principal que ejecuta el proyecto
├── recoleccion.py         # Script para extraer y limpiar datos
├── dashboard_inegi.py     # Dashboard interactivo con Streamlit
└── api_inegi/             # Carpeta donde se guardan los archivos CSV generados

🚀 ¿Qué hace main.py?

El archivo main.py controla todo el flujo del proyecto:

Verifica que exista recoleccion.py

Ejecuta automáticamente el proceso de recolección de datos

Lanza el dashboard en Streamlit para la visualización

Todo se ejecuta con un solo comando.

🧰 Requisitos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

Python 3.10 o superior

Las siguientes librerías:

pip install streamlit pandas matplotlib pyodbc


Además, si usas SQL Server, debes tener instalado:

ODBC Driver 17 for SQL Server

▶️ Cómo ejecutar el proyecto

Dentro de la carpeta del proyecto, ejecuta:

python main.py

🛠 Posibles errores comunes
🔹 Error: No module named 'pyodbc'

Solución:

pip install pyodbc

🔹 Error: ODBC Driver 17 for SQL Server no encontrado

Solución:
Instalar el driver oficial de Microsoft para SQL Server.

📊 Tecnologías usadas

Python

Streamlit

Pandas

Matplotlib

SQL Server

GitHub
