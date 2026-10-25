# AnaliticaBI UMB

Aplicación de escritorio para **ingresar datos, validarlos y generar gráficos automáticamente**.
Desarrollada para la **Guía de Laboratorio No. 9** del módulo *Inteligencia de Negocios Avanzada y Toma de Decisiones* (eje temático: Business Analytics e Inteligencia Artificial) de la **Universidad Manuela Beltrán (UMB)**.

- Aplicación **nativa de escritorio** (Python + Tkinter). No es web, ni PWA, ni usa HTML/CSS/JavaScript.
- Funciona **100 % sin conexión a internet**.
- **Portable**: se puede empaquetar en un solo `.exe` que corre sin instalar nada.

---

## ¿Qué hace?

| Función | Descripción |
|---|---|
| Datos precargados | Incluye la encuesta oficial de la guía: 100 estudiantes y sus actividades de tiempo libre. |
| Ingreso de datos | Formulario para agregar, actualizar y eliminar actividades. |
| Validación | Rechaza campos vacíos, texto en lugar de números, decimales, ceros y negativos. |
| Dataset protegido | La encuesta original no se puede modificar por accidente (trazabilidad). Se puede crear una **copia editable** o un **dataset vacío**. |
| Tabla de frecuencias | Cantidad, porcentaje y porcentaje acumulado de cada categoría. |
| Gráficos automáticos | Barras verticales, circular (dona), barras horizontales y diagrama de Pareto. |
| Indicadores (KPI) | Total, actividad más y menos frecuente, promedio y rango. |
| Importar / exportar | Lee y guarda archivos CSV. El gráfico también se guarda como PNG. |
| Informe Fase 1 | Respuestas a las preguntas, reto de pensamiento crítico y conclusiones. |
| Pruebas | Pruebas automáticas que se ejecutan desde la propia aplicación. |
| Ejecutable | Botón para generar `AnaliticaBI_UMB.exe` portable. |

---

## Archivos del proyecto

```
AnaliticaBI_UMB_App.py       ← la aplicación (todo el código)
Abrir_AnaliticaBI_UMB.bat    ← lanzador para Windows (instala lo necesario y abre la app)
README.md                    ← este archivo
datos/                       ← se crea sola al abrir la app (datos guardados)
```

---

## Cómo usarla (Windows) — la forma fácil

1. Descarga los archivos del repositorio (**Code → Download ZIP**) y descomprímelos.
2. Asegúrate de que `AnaliticaBI_UMB_App.py` y `Abrir_AnaliticaBI_UMB.bat` estén **en la misma carpeta**.
3. Haz **doble clic** en `Abrir_AnaliticaBI_UMB.bat`.

La primera vez, el lanzador:

1. Busca Python en tu equipo.
2. Si no lo encuentra, lo instala automáticamente con `winget` (tarda 1 a 3 minutos; no cierres la ventana).
3. Instala las librerías `pandas` y `matplotlib` si faltan.
4. Abre la aplicación.

Las siguientes veces abre directo.

> Si `winget` no existe en tu Windows, instala Python a mano desde <https://www.python.org/downloads/> y marca la casilla **"Add Python to PATH"**. Luego abre el `.bat` otra vez.

---

## Cómo usarla desde la terminal (Windows, macOS o Linux)

Requisitos: **Python 3.9 o superior** con Tkinter.

```bash
pip install pandas matplotlib
python AnaliticaBI_UMB_App.py
```

> En Linux, si falta Tkinter: `sudo apt install python3-tk`.

---

## Cómo generar el `.exe` portable

El `.exe` se puede copiar a otro computador y funciona **sin instalar Python**.

**Opción A: desde la aplicación**

1. Abre la app y ve a la pestaña **Guía y Pruebas**.
2. Pulsa **Generar .exe** y espera de 1 a 3 minutos (puedes seguir usando la app).
3. El archivo `AnaliticaBI_UMB.exe` aparece en la misma carpeta.

**Opción B: desde la terminal**

```bash
pip install pyinstaller pandas matplotlib
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "AnaliticaBI_UMB" ^
  --hidden-import pandas --hidden-import matplotlib.backends.backend_tkagg AnaliticaBI_UMB_App.py
```

El resultado queda en `dist/AnaliticaBI_UMB.exe`.

> El `.exe` crea una carpeta `datos` junto a él para guardar la información. Si lo mueves, mueve también esa carpeta para conservar tus datos.

---

## Guía rápida de uso

1. **Ver los datos oficiales:** al abrir, verás la encuesta de 100 estudiantes y el gráfico.
2. **Cambiar de gráfico:** usa los botones *Barras, Circular, Horizontal, Pareto*.
3. **Agregar tus propios datos:**
   - Pulsa **Nueva copia** (copia la encuesta oficial para editarla) o **Dataset vacío**.
   - Escribe la actividad y el número de estudiantes, y pulsa **Guardar** (o Enter).
   - El gráfico y las tablas se actualizan solos.
4. **Editar o eliminar:** haz clic en una fila de la tabla, cámbiala y pulsa **Guardar**, o pulsa **Eliminar**.
5. **Guardar resultados:** **Exportar** crea un CSV, **Guardar PNG** guarda el gráfico.
6. **Volver al inicio:** **Restaurar** devuelve los datos originales de la guía.

### Formato del CSV para importar

La primera fila es el encabezado y cada fila siguiente tiene la actividad y la cantidad de estudiantes (número entero mayor que cero):

```csv
actividad,estudiantes
Ver series o películas,28
Escuchar música,22
Practicar deporte,18
```

---

## Pruebas automáticas

Desde la app: pestaña **Guía y Pruebas → Ejecutar pruebas**.

Desde la terminal:

```bash
python AnaliticaBI_UMB_App.py --test
```

Las pruebas verifican la muestra de 100 estudiantes, las validaciones, la protección del dataset oficial, la creación de datasets nuevos, la importación/exportación CSV y que los porcentajes sumen 100 %.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| El `.bat` dice que no encuentra `AnaliticaBI_UMB_App.py` | Pon los dos archivos en la misma carpeta (y descomprime el ZIP antes de abrirlos). |
| "No se encontro Python instalado" | Instálalo desde python.org marcando **Add Python to PATH**. |
| "Tu Python no trae tkinter" | Reinstala Python y deja marcada la opción **tcl/tk and IDLE**. |
| Windows muestra un aviso de seguridad al abrir el `.exe` | Es normal con programas sin firma digital. Pulsa *Más información → Ejecutar de todas formas*. |
| El botón "Generar .exe" falla | Instala PyInstaller: `pip install pyinstaller`. |

---

## Tecnologías

- Python 3
- Tkinter / ttk (interfaz gráfica)
- Matplotlib (gráficos)
- Pandas (cálculo de frecuencias y porcentajes)
- PyInstaller (ejecutable portable)

---

## Créditos

Universidad Manuela Beltrán (UMB) · Guía de Laboratorio No. 9 · Business Analytics e Inteligencia Artificial.

**Integrantes:** _(escribe aquí los nombres del grupo)_
