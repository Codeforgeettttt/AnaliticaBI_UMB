# -*- coding: utf-8 -*-
"""
=============================================================================
UNIVERSIDAD MANUELA BELTRÁN (UMB)
Módulo: Inteligencia de Negocios Avanzada y Toma de Decisiones
Eje Temático: Business Analytics e Inteligencia Artificial
Guía de Laboratorio No. 9 - Sesión 11 / Semana 11
-----------------------------------------------------------------------------
Archivo: AnaliticaBI_UMB_App.py
Descripción:
    Aplicación de escritorio nativa y portable para Windows desarrollada en
    Python con Tkinter (ttk), Matplotlib y Pandas.
    - Aplicación de escritorio 100% nativa (NO web, NO PWA, NO HTML/CSS/JS).
    - Funciona 100% sin conexión a internet.
    - Precarga los datos de la encuesta de 100 estudiantes (Fase 1).
    - Permite crear conjuntos de datos nuevos sin alterar el original.
    - Incluye CRUD completo, validaciones, tabla de frecuencias, generación
      automatizada de 4 tipos de gráficas, importación/exportación CSV,
      almacenamiento local JSON, pruebas automatizadas y empaquetador .EXE.
=============================================================================
"""

import os
import sys
import json
import csv
import io
import shutil
import subprocess
import tempfile
import textwrap
import threading
import unittest
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter import font as tkfont

try:
    import pandas as pd
    PANDAS_DISPONIBLE = True
except ImportError:
    PANDAS_DISPONIBLE = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Patch
    from matplotlib.ticker import PercentFormatter
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


NOMBRE_DATASET_OFICIAL = "Encuesta Oficial Guía 9 (100 Estudiantes)"

DATOS_OFICIALES_GUIA_9 = [
    {"actividad": "Ver series o películas", "estudiantes": 28},
    {"actividad": "Escuchar música", "estudiantes": 22},
    {"actividad": "Practicar deporte", "estudiantes": 18},
    {"actividad": "Jugar videojuegos", "estudiantes": 15},
    {"actividad": "Leer", "estudiantes": 10},
    {"actividad": "Otras actividades", "estudiantes": 7},
]

PALETA_COLORES = [
    "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444",
    "#06B6D4", "#EC4899", "#84CC16", "#6366F1", "#64748B",
]


def obtener_ruta_base() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class GestorDatosBI:
    def __init__(self, ruta_almacenamiento: str = None):
        base_dir = obtener_ruta_base()
        carpeta_datos = os.path.join(base_dir, "datos")
        os.makedirs(carpeta_datos, exist_ok=True)
        self.ruta_json = ruta_almacenamiento or os.path.join(
            carpeta_datos, "almacenamiento_local.json"
        )
        self.datasets = {}
        self.dataset_actual = NOMBRE_DATASET_OFICIAL
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self) -> None:
        if os.path.exists(self.ruta_json):
            try:
                with open(self.ruta_json, "r", encoding="utf-8") as f:
                    contenido = json.load(f)
                    if isinstance(contenido, dict) and "datasets" in contenido:
                        self.datasets = contenido["datasets"]
                        self.dataset_actual = contenido.get(
                            "dataset_actual", NOMBRE_DATASET_OFICIAL
                        )
            except Exception:
                self.datasets = {}

        if NOMBRE_DATASET_OFICIAL not in self.datasets:
            self.datasets[NOMBRE_DATASET_OFICIAL] = [
                dict(item) for item in DATOS_OFICIALES_GUIA_9
            ]
        if self.dataset_actual not in self.datasets:
            self.dataset_actual = NOMBRE_DATASET_OFICIAL

        self.guardar_json()
        self._exportar_csv_semilla_si_no_existe()

    def _exportar_csv_semilla_si_no_existe(self) -> None:
        ruta_csv = os.path.join(
            os.path.dirname(self.ruta_json), "encuesta_100_estudiantes.csv"
        )
        if not os.path.exists(ruta_csv):
            try:
                with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=["actividad", "estudiantes"])
                    writer.writeheader()
                    writer.writerows(DATOS_OFICIALES_GUIA_9)
            except Exception:
                pass

    def guardar_json(self) -> bool:
        try:
            payload = {
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dataset_actual": self.dataset_actual,
                "datasets": self.datasets,
            }
            with open(self.ruta_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def validar_registro(actividad: str, valor_str: str) -> tuple:
        if actividad is None or not str(actividad).strip():
            return False, "El nombre de la actividad o categoría no puede estar vacío.", 0
        actividad_limpia = str(actividad).strip()
        if len(actividad_limpia) > 80:
            return False, "El nombre de la actividad no debe superar 80 caracteres.", 0
        if valor_str is None or not str(valor_str).strip():
            return False, "Debe ingresar un número de estudiantes (frecuencia).", 0
        texto_num = str(valor_str).strip()
        if "." in texto_num or "," in texto_num:
            return False, "La cantidad de estudiantes debe ser un número entero exacto (sin decimales).", 0
        try:
            cantidad = int(texto_num)
        except ValueError:
            return False, f"El valor '{texto_num}' no es un número entero válido.", 0
        if cantidad <= 0:
            return False, "La cantidad de estudiantes debe ser un número entero mayor que cero (> 0).", 0
        if cantidad > 1000000:
            return False, "El valor ingresado excede el límite máximo permitido (1,000,000).", 0
        return True, "", cantidad

    def crear_dataset(self, nombre: str, copiar_actual: bool = False) -> tuple:
        nombre_limpio = str(nombre).strip()
        if not nombre_limpio:
            return False, "El nombre del conjunto de datos no puede estar vacío."
        if nombre_limpio in self.datasets:
            return False, f"Ya existe un conjunto de datos llamado '{nombre_limpio}'."
        if copiar_actual and self.dataset_actual in self.datasets:
            self.datasets[nombre_limpio] = [
                dict(r) for r in self.datasets[self.dataset_actual]
            ]
        else:
            self.datasets[nombre_limpio] = []
        self.dataset_actual = nombre_limpio
        self.guardar_json()
        return True, f"Conjunto de datos '{nombre_limpio}' creado exitosamente."

    def eliminar_dataset(self, nombre: str) -> tuple:
        if nombre == NOMBRE_DATASET_OFICIAL:
            return False, "No se permite eliminar el dataset oficial de la Guía 9."
        if nombre not in self.datasets:
            return False, "El conjunto de datos seleccionado no existe."
        del self.datasets[nombre]
        self.dataset_actual = NOMBRE_DATASET_OFICIAL
        self.guardar_json()
        return True, f"Conjunto de datos '{nombre}' eliminado correctamente."

    def restaurar_dataset_oficial(self) -> None:
        self.datasets[NOMBRE_DATASET_OFICIAL] = [
            dict(item) for item in DATOS_OFICIALES_GUIA_9
        ]
        self.dataset_actual = NOMBRE_DATASET_OFICIAL
        self.guardar_json()

    def agregar_o_actualizar_registro(
        self, actividad: str, valor_str: str, permitir_edicion_oficial: bool = False
    ) -> tuple:
        valido, msg, cantidad = self.validar_registro(actividad, valor_str)
        if not valido:
            return False, msg
        if self.dataset_actual == NOMBRE_DATASET_OFICIAL and not permitir_edicion_oficial:
            return (
                False,
                "PROTECCIÓN DE TRAZABILIDAD: El ejemplo original de 100 estudiantes está protegido. "
                "Haga clic en '+ Copia Editable' arriba a la derecha o active la casilla de edición.",
            )
        actividad_limpia = actividad.strip()
        registros = self.datasets.setdefault(self.dataset_actual, [])
        for reg in registros:
            if reg["actividad"].strip().lower() == actividad_limpia.lower():
                reg["actividad"] = actividad_limpia
                reg["estudiantes"] = cantidad
                self.guardar_json()
                return True, f"Registro '{actividad_limpia}' actualizado a {cantidad}."
        registros.append({"actividad": actividad_limpia, "estudiantes": cantidad})
        self.guardar_json()
        return True, f"Actividad '{actividad_limpia}' agregada con {cantidad} estudiantes."

    def eliminar_registro(
        self, actividad: str, permitir_edicion_oficial: bool = False
    ) -> tuple:
        if self.dataset_actual == NOMBRE_DATASET_OFICIAL and not permitir_edicion_oficial:
            return (
                False,
                "No se pueden eliminar filas del dataset oficial protegido sin crear una copia o activar edición.",
            )
        registros = self.datasets.get(self.dataset_actual, [])
        nuevos = [
            r for r in registros
            if r["actividad"].strip().lower() != str(actividad).strip().lower()
        ]
        if len(nuevos) == len(registros):
            return False, f"No se encontró la actividad '{actividad}'."
        self.datasets[self.dataset_actual] = nuevos
        self.guardar_json()
        return True, f"Actividad '{actividad}' eliminada."

    def obtener_registros_enriquecidos(self, ordenar_desc: bool = False) -> list:
        registros = [dict(r) for r in self.datasets.get(self.dataset_actual, [])]
        if not registros:
            return []
        if ordenar_desc:
            registros.sort(key=lambda x: int(x["estudiantes"]), reverse=True)
        if PANDAS_DISPONIBLE:
            df = pd.DataFrame(registros)
            df["estudiantes"] = pd.to_numeric(df["estudiantes"], errors="coerce").fillna(0).astype(int)
            total = int(df["estudiantes"].sum())
            df["porcentaje"] = (df["estudiantes"] / total * 100.0).round(2) if total > 0 else 0.0
            df["acumulado"] = df["estudiantes"].cumsum()
            df["porcentaje_acumulado"] = (df["acumulado"] / total * 100.0).round(2) if total > 0 else 0.0
            return df.to_dict(orient="records")
        total = sum(int(r["estudiantes"]) for r in registros)
        acum = 0
        resultado = []
        for r in registros:
            est = int(r["estudiantes"])
            acum += est
            pct = round((est / total * 100.0), 2) if total > 0 else 0.0
            pct_acum = round((acum / total * 100.0), 2) if total > 0 else 0.0
            resultado.append({
                "actividad": r["actividad"],
                "estudiantes": est,
                "porcentaje": pct,
                "acumulado": acum,
                "porcentaje_acumulado": pct_acum,
            })
        return resultado

    def calcular_estadisticas(self) -> dict:
        filas = self.obtener_registros_enriquecidos(ordenar_desc=False)
        if not filas:
            return {
                "total_estudiantes": 0, "num_categorias": 0,
                "actividad_mayor": "Sin datos", "valor_mayor": 0, "porcentaje_mayor": 0.0,
                "actividad_menor": "Sin datos", "valor_menor": 0, "porcentaje_menor": 0.0,
                "promedio": 0.0, "rango": 0, "actividades_mas_de_15": [],
            }
        total = sum(f["estudiantes"] for f in filas)
        fila_max = max(filas, key=lambda x: x["estudiantes"])
        fila_min = min(filas, key=lambda x: x["estudiantes"])
        mas_de_15 = [f["actividad"] for f in filas if f["estudiantes"] > 15]
        promedio = round(total / len(filas), 2)
        return {
            "total_estudiantes": total,
            "num_categorias": len(filas),
            "actividad_mayor": fila_max["actividad"],
            "valor_mayor": fila_max["estudiantes"],
            "porcentaje_mayor": fila_max["porcentaje"],
            "actividad_menor": fila_min["actividad"],
            "valor_menor": fila_min["estudiantes"],
            "porcentaje_menor": fila_min["porcentaje"],
            "promedio": promedio,
            "rango": fila_max["estudiantes"] - fila_min["estudiantes"],
            "actividades_mas_de_15": mas_de_15,
        }

    def importar_csv(self, ruta_archivo: str, nombre_nuevo_dataset: str = None) -> tuple:
        if not os.path.exists(ruta_archivo):
            return False, "El archivo CSV seleccionado no existe."
        filas_leidas = []
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                with open(ruta_archivo, "r", encoding=enc, newline="") as f:
                    lector = csv.reader(f)
                    filas_leidas = [row for row in lector if any(c.strip() for c in row)]
                break
            except Exception:
                continue
        if len(filas_leidas) < 2:
            return False, "El archivo CSV debe tener encabezado y al menos una fila de datos."
        registros_validados = []
        for idx, fila in enumerate(filas_leidas[1:], start=2):
            if len(fila) < 2:
                return False, f"La fila {idx} no tiene al menos 2 columnas."
            act, val = fila[0].strip(), fila[1].strip()
            ok, msg, num = self.validar_registro(act, val)
            if not ok:
                return False, f"Error en fila {idx} ({act}): {msg}"
            registros_validados.append({"actividad": act, "estudiantes": num})
        nombre_destino = nombre_nuevo_dataset or (
            f"Importado - {os.path.splitext(os.path.basename(ruta_archivo))[0]}"
        )
        base_nombre = nombre_destino
        contador = 2
        while nombre_destino in self.datasets:
            nombre_destino = f"{base_nombre} ({contador})"
            contador += 1
        self.datasets[nombre_destino] = registros_validados
        self.dataset_actual = nombre_destino
        self.guardar_json()
        return True, f"Se importaron {len(registros_validados)} registros en '{nombre_destino}'."

    def exportar_csv(self, ruta_destino: str) -> tuple:
        filas = self.obtener_registros_enriquecidos()
        if not filas:
            return False, "No hay datos para exportar."
        try:
            with open(ruta_destino, "w", newline="", encoding="utf-8-sig") as f:
                campos = ["actividad", "estudiantes", "porcentaje", "acumulado", "porcentaje_acumulado"]
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                writer.writerows(filas)
            return True, f"Archivo CSV exportado correctamente en:\n{ruta_destino}"
        except Exception as e:
            return False, f"Error al exportar CSV: {e}"


# =============================================================================
# TEMA VISUAL (colores centralizados para toda la interfaz)
# =============================================================================
C_NAVY = "#0F172A"
C_BG = "#F3F5F9"
C_CARD = "#FFFFFF"
C_BORDE = "#E2E8F0"
C_TEXTO = "#0F172A"
C_SUAVE = "#64748B"
C_PRIM = "#2563EB"
C_PRIM_H = "#1D4ED8"
C_OK = "#059669"
C_PELIGRO = "#DC2626"
C_UMB = "#B91C1C"
C_AMBAR_BG = "#FEF3C7"
C_AMBAR = "#92400E"

TIPOS_GRAFICO = [
    ("Barras", "Barras Verticales (Frecuencias)"),
    ("Circular", "Gráfico Circular / Pastel (Porcentajes)"),
    ("Horizontal", "Barras Horizontales (Comparativo)"),
    ("Pareto", "Diagrama de Pareto (Frecuencia + % Acumulado)"),
]


class AplicacionAnaliticaBI:
    """Interfaz gráfica principal (Tkinter/ttk). La lógica vive en GestorDatosBI."""

    def __init__(self, root: tk.Tk, gestor: GestorDatosBI = None):
        self.root = root
        self.F = self._elegir_fuente()
        self.root.title("AnaliticaBI UMB · Business Analytics e Inteligencia Artificial (Guía 9)")
        self._centrar_ventana(1320, 840)
        self.root.minsize(1100, 740)
        self.root.configure(bg=C_BG)
        self.gestor = gestor or GestorDatosBI()

        self.var_dataset = tk.StringVar(value=self.gestor.dataset_actual)
        self.var_tipo_grafico = tk.StringVar(value=TIPOS_GRAFICO[0][1])
        self.var_actividad = tk.StringVar()
        self.var_estudiantes = tk.StringVar()
        self.var_permitir_edicion_oficial = tk.BooleanVar(value=False)
        self.var_mostrar_etiquetas = tk.BooleanVar(value=True)
        self.var_ordenar_desc = tk.BooleanVar(value=False)
        self._id_estado = None
        self._resultado_compilacion = None

        if MATPLOTLIB_DISPONIBLE:
            matplotlib.rcParams["font.family"] = "sans-serif"
            matplotlib.rcParams["font.sans-serif"] = [self.F, "Segoe UI", "DejaVu Sans", "Arial"]

        self._configurar_estilos()
        self._construir_encabezado()
        self._construir_barra_estado()
        self._construir_paginas()
        self.mostrar_pestana("dashboard")
        self.actualizar_vista_completa()

    # ------------------------------------------------------------------ base
    def _elegir_fuente(self) -> str:
        familias = set(tkfont.families(self.root))
        for nombre in ("Segoe UI", "Helvetica Neue", "Inter", "Ubuntu", "DejaVu Sans", "Arial"):
            if nombre in familias:
                return nombre
        return "TkDefaultFont"

    def f(self, tam: int, negrita: bool = False) -> tuple:
        return (self.F, tam, "bold") if negrita else (self.F, tam)

    def _centrar_ventana(self, ancho: int, alto: int) -> None:
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = min(ancho, int(sw * 0.94)), min(alto, int(sh * 0.90))
        x, y = (sw - w) // 2, max(0, (sh - h) // 2 - 10)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _tarjeta(self, parent: tk.Widget, bg: str = C_CARD) -> tk.Frame:
        return tk.Frame(parent, bg=bg, highlightbackground=C_BORDE, highlightcolor=C_BORDE,
                        highlightthickness=1, bd=0)

    def _boton(self, parent, texto, comando, estilo="Ghost.TButton") -> ttk.Button:
        return ttk.Button(parent, text=texto, command=comando, style=estilo, cursor="hand2")

    def _configurar_estilos(self) -> None:
        e = ttk.Style(self.root)
        try:
            e.theme_use("clam")
        except Exception:
            pass
        self.root.option_add("*TCombobox*Listbox.font", self.f(10))
        self.root.option_add("*TCombobox*Listbox.selectBackground", C_PRIM)

        def boton(nombre, bg, fg, hover, borde=None):
            b = borde or bg
            e.configure(nombre, background=bg, foreground=fg, font=self.f(9, True), padding=(14, 8),
                        borderwidth=1, bordercolor=b, lightcolor=b, darkcolor=b, focuscolor=bg)
            e.map(nombre, background=[("disabled", "#E2E8F0"), ("pressed", hover), ("active", hover)],
                  foreground=[("disabled", "#94A3B8")])

        boton("Primario.TButton", C_PRIM, "#FFFFFF", C_PRIM_H)
        boton("Exito.TButton", C_OK, "#FFFFFF", "#047857")
        boton("Oscuro.TButton", C_NAVY, "#FFFFFF", "#1E293B")
        boton("Peligro.TButton", "#FFFFFF", C_PELIGRO, "#FEF2F2", "#FCA5A5")
        boton("Ghost.TButton", "#FFFFFF", C_TEXTO, "#F1F5F9", "#CBD5E1")
        boton("Aviso.TButton", "#FFFFFF", C_AMBAR, "#FFF7E0", "#F5D58A")

        for nombre in ("Campo.TEntry", "Campo.TCombobox"):
            e.configure(nombre, padding=(10, 8), fieldbackground="#FFFFFF", background="#FFFFFF",
                        foreground=C_TEXTO, bordercolor="#CBD5E1", lightcolor="#CBD5E1", darkcolor="#CBD5E1",
                        borderwidth=1, arrowcolor=C_SUAVE)
        e.map("Campo.TEntry", bordercolor=[("focus", C_PRIM)], lightcolor=[("focus", C_PRIM)], darkcolor=[("focus", C_PRIM)])
        e.map("Campo.TCombobox", fieldbackground=[("readonly", "#FFFFFF")], selectbackground=[("readonly", "#FFFFFF")],
              selectforeground=[("readonly", C_TEXTO)], bordercolor=[("focus", C_PRIM)])

        e.configure("Seg.Toolbutton", background="#EEF2F7", foreground=C_TEXTO, font=self.f(9, True),
                    padding=(16, 7), borderwidth=0, relief="flat", bordercolor="#EEF2F7",
                    lightcolor="#EEF2F7", darkcolor="#EEF2F7", focuscolor="#EEF2F7")
        e.map("Seg.Toolbutton", background=[("selected", C_PRIM), ("active", "#DCE4F0")],
              foreground=[("selected", "#FFFFFF")], bordercolor=[("selected", C_PRIM)],
              lightcolor=[("selected", C_PRIM)], darkcolor=[("selected", C_PRIM)])

        e.configure("Card.TCheckbutton", background=C_CARD, foreground=C_TEXTO, font=self.f(9))
        e.map("Card.TCheckbutton", background=[("active", C_CARD)])
        e.configure("Aviso.TCheckbutton", background=C_AMBAR_BG, foreground=C_AMBAR, font=self.f(9, True))
        e.map("Aviso.TCheckbutton", background=[("active", C_AMBAR_BG)])

        e.layout("Tabla.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        e.configure("Tabla.Treeview", font=self.f(10), rowheight=30, background="#FFFFFF",
                    fieldbackground="#FFFFFF", foreground=C_TEXTO, borderwidth=0)
        e.map("Tabla.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])
        e.configure("Tabla.Treeview.Heading", font=self.f(9, True), background="#EEF2F7", foreground=C_SUAVE,
                    relief="flat", padding=(8, 8), borderwidth=0)
        e.map("Tabla.Treeview.Heading", background=[("active", "#E2E8F0")])
        e.configure("Vertical.TScrollbar", background="#CBD5E1", troughcolor="#F1F5F9", bordercolor="#F1F5F9",
                    arrowcolor=C_SUAVE, relief="flat", gripcount=0)

    # ------------------------------------------------------------ estructura
    def _construir_encabezado(self) -> None:
        header = tk.Frame(self.root, bg=C_NAVY)
        header.pack(fill="x", side="top")
        fila = tk.Frame(header, bg=C_NAVY)
        fila.pack(fill="x", padx=24)
        tk.Label(fila, text="UMB", font=self.f(13, True), bg=C_UMB, fg="#FFFFFF", padx=12, pady=6).pack(side="left", pady=10)
        textos = tk.Frame(fila, bg=C_NAVY)
        textos.pack(side="left", padx=14)
        tk.Label(textos, text="AnaliticaBI UMB", font=self.f(15, True), bg=C_NAVY, fg="#FFFFFF").pack(anchor="w")
        tk.Label(textos, text="Business Analytics e Inteligencia Artificial  ·  Guía de Laboratorio No. 9",
                 font=self.f(9), bg=C_NAVY, fg="#94A3B8").pack(anchor="w")

        nav = tk.Frame(fila, bg=C_NAVY)
        nav.pack(side="right", anchor="s")
        self.nav = {}
        for clave, texto in (("dashboard", "Dashboard"), ("informe", "Informe Fase 1"), ("guia", "Guía y Pruebas")):
            cont = tk.Frame(nav, bg=C_NAVY, cursor="hand2")
            cont.pack(side="left")
            lbl = tk.Label(cont, text=texto, font=self.f(10, True), bg=C_NAVY, fg="#94A3B8", padx=16, pady=10)
            lbl.pack()
            linea = tk.Frame(cont, bg=C_NAVY, height=3)
            linea.pack(fill="x")
            for w in (cont, lbl):
                w.bind("<Button-1>", lambda _e, k=clave: self.mostrar_pestana(k))
            self.nav[clave] = (lbl, linea)

    def _construir_barra_estado(self) -> None:
        barra = tk.Frame(self.root, bg="#E8ECF2")
        barra.pack(fill="x", side="bottom")
        self.lbl_estado = tk.Label(barra, text="Listo.", font=self.f(9), bg="#E8ECF2", fg=C_SUAVE, anchor="w", padx=20, pady=5)
        self.lbl_estado.pack(side="left")
        tk.Label(barra, text="100 % offline  ·  portable  ·  autoguardado activo", font=self.f(9), bg="#E8ECF2", fg=C_SUAVE, padx=20).pack(side="right")

    def _estado(self, texto: str, tipo: str = "ok") -> None:
        color = {"ok": C_OK, "error": C_PELIGRO, "info": C_SUAVE}.get(tipo, C_SUAVE)
        self.lbl_estado.config(text=texto.replace("\n", " "), fg=color)
        if self._id_estado:
            self.root.after_cancel(self._id_estado)
        self._id_estado = self.root.after(7000, lambda: self.lbl_estado.config(text="Listo.", fg=C_SUAVE))

    def _construir_paginas(self) -> None:
        self.contenedor = tk.Frame(self.root, bg=C_BG)
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.tab_dashboard = tk.Frame(self.contenedor, bg=C_BG)
        self.tab_fase1 = tk.Frame(self.contenedor, bg=C_BG)
        self.tab_arquitectura = tk.Frame(self.contenedor, bg=C_BG)
        self.paginas = {"dashboard": self.tab_dashboard, "informe": self.tab_fase1, "guia": self.tab_arquitectura}
        for p in self.paginas.values():
            p.grid(row=0, column=0, sticky="nsew")
        self._construir_tab_dashboard()
        self._construir_tab_fase1()
        self._construir_tab_arquitectura()

    def mostrar_pestana(self, clave: str) -> None:
        self.paginas[clave].tkraise()
        for k, (lbl, linea) in self.nav.items():
            activa = k == clave
            lbl.config(fg="#FFFFFF" if activa else "#94A3B8")
            linea.config(bg=C_UMB if activa else C_NAVY)

    # ------------------------------------------------------------- dashboard
    def _construir_tab_dashboard(self) -> None:
        pag = self.tab_dashboard
        pag.grid_columnconfigure(0, weight=1)
        pag.grid_rowconfigure(2, weight=1)

        # --- barra de conjuntos de datos
        barra = self._tarjeta(pag)
        barra.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 10))
        fila = tk.Frame(barra, bg=C_CARD)
        fila.pack(fill="x", padx=14, pady=8)
        self._boton(fila, "Eliminar", self.evento_eliminar_dataset, "Peligro.TButton").pack(side="right")
        self._boton(fila, "Restaurar", self.evento_restaurar_oficial).pack(side="right", padx=6)
        self._boton(fila, "Dataset vacío", lambda: self.evento_crear_dataset(copiar=False)).pack(side="right")
        self._boton(fila, "Nueva copia", lambda: self.evento_crear_dataset(copiar=True), "Primario.TButton").pack(side="right", padx=6)
        tk.Label(fila, text="Dataset", font=self.f(9, True), bg=C_CARD, fg=C_SUAVE).pack(side="left")
        self.combo_datasets = ttk.Combobox(fila, textvariable=self.var_dataset, state="readonly", width=34,
                                           style="Campo.TCombobox", font=self.f(10))
        self.combo_datasets.pack(side="left", padx=10)
        self.combo_datasets.bind("<<ComboboxSelected>>", self.evento_cambiar_dataset)
        self.lbl_badge = tk.Label(fila, text="", font=self.f(8, True), padx=10, pady=4)
        self.lbl_badge.pack(side="left")

        # --- KPIs
        kpis = tk.Frame(pag, bg=C_BG)
        kpis.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        for i in range(4):
            kpis.grid_columnconfigure(i, weight=1, uniform="kpi")
        self.kpi_total = self._crear_tarjeta_kpi(kpis, "MUESTRA TOTAL (N)", "#2563EB", 0)
        self.kpi_mayor = self._crear_tarjeta_kpi(kpis, "MÁS FRECUENTE (MODA)", "#059669", 1)
        self.kpi_menor = self._crear_tarjeta_kpi(kpis, "MENOS FRECUENTE", "#D97706", 2)
        self.kpi_promedio = self._crear_tarjeta_kpi(kpis, "PROMEDIO POR CATEGORÍA", "#7C3AED", 3)

        # --- cuerpo
        cuerpo = tk.Frame(pag, bg=C_BG)
        cuerpo.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 16))
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(0, weight=0, minsize=450)
        cuerpo.grid_columnconfigure(1, weight=1)
        izq = self._tarjeta(cuerpo)
        izq.configure(width=450)
        izq.grid_propagate(False)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        der = self._tarjeta(cuerpo)
        der.grid(row=0, column=1, sticky="nsew")
        self._construir_panel_datos(izq)
        self._construir_panel_grafico(der)

    def _crear_tarjeta_kpi(self, parent, titulo: str, color: str, col: int) -> tuple:
        card = self._tarjeta(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0 if col == 3 else 6))
        tk.Frame(card, bg=color, width=5).pack(side="left", fill="y")
        cuerpo = tk.Frame(card, bg=C_CARD)
        cuerpo.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        tk.Label(cuerpo, text=titulo, font=self.f(8, True), bg=C_CARD, fg=C_SUAVE).pack(anchor="w")
        valor = tk.Label(cuerpo, text="—", font=self.f(13, True), bg=C_CARD, fg=C_TEXTO, anchor="w", justify="left")
        valor.pack(anchor="w", fill="x", pady=(3, 0))
        sub = tk.Label(cuerpo, text="", font=self.f(9), bg=C_CARD, fg=C_SUAVE, anchor="w")
        sub.pack(anchor="w", fill="x")
        cuerpo.bind("<Configure>", lambda e, v=valor: v.config(wraplength=max(120, e.width - 6)))
        return valor, sub

    def _construir_panel_datos(self, panel: tk.Frame) -> None:
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(8, weight=1)
        pad = dict(padx=16)
        tk.Label(panel, text="Registrar datos", font=self.f(12, True), bg=C_CARD, fg=C_TEXTO).grid(row=0, column=0, sticky="w", pady=(14, 8), **pad)

        # aviso de protección del dataset oficial
        self.aviso = tk.Frame(panel, bg=C_AMBAR_BG, highlightbackground="#F5D58A", highlightthickness=1)
        self.aviso.grid(row=1, column=0, sticky="ew", pady=(0, 6), **pad)
        self.lbl_aviso = tk.Label(self.aviso, text="", font=self.f(9), bg=C_AMBAR_BG, fg=C_AMBAR, justify="left", anchor="w")
        self.lbl_aviso.pack(fill="x", padx=12, pady=(8, 4))
        self.aviso.bind("<Configure>", lambda e: self.lbl_aviso.config(wraplength=max(160, e.width - 28)))
        acc = tk.Frame(self.aviso, bg=C_AMBAR_BG)
        acc.pack(fill="x", padx=12, pady=(0, 8))
        self._boton(acc, "Crear copia editable", lambda: self.evento_crear_dataset(copiar=True), "Aviso.TButton").pack(side="left")
        ttk.Checkbutton(acc, text="Desbloquear", variable=self.var_permitir_edicion_oficial,
                        command=self._actualizar_estado_edicion, style="Aviso.TCheckbutton").pack(side="left", padx=12)

        form = tk.Frame(panel, bg=C_CARD)
        form.grid(row=2, column=0, sticky="ew", pady=(0, 2), **pad)
        form.grid_columnconfigure(0, weight=3)
        form.grid_columnconfigure(1, weight=1)
        tk.Label(form, text="Actividad o categoría", font=self.f(9, True), bg=C_CARD, fg=C_SUAVE).grid(row=0, column=0, sticky="w")
        tk.Label(form, text="Estudiantes", font=self.f(9, True), bg=C_CARD, fg=C_SUAVE).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.entry_actividad = ttk.Entry(form, textvariable=self.var_actividad, style="Campo.TEntry", font=self.f(10))
        self.entry_actividad.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.entry_estudiantes = ttk.Entry(form, textvariable=self.var_estudiantes, style="Campo.TEntry", font=self.f(10), width=8)
        self.entry_estudiantes.grid(row=1, column=1, sticky="ew", pady=(3, 0), padx=(8, 0))
        for ent in (self.entry_actividad, self.entry_estudiantes):
            ent.bind("<Return>", lambda _e: self.evento_agregar_actualizar())

        self.lbl_form_msg = tk.Label(panel, text="", font=self.f(9), bg=C_CARD, fg=C_PELIGRO, justify="left", anchor="w")
        self.lbl_form_msg.grid(row=3, column=0, sticky="ew", **pad)
        panel.bind("<Configure>", lambda e: self.lbl_form_msg.config(wraplength=max(160, e.width - 36)))

        botones = tk.Frame(panel, bg=C_CARD)
        botones.grid(row=4, column=0, sticky="ew", pady=(2, 10), **pad)
        self._boton(botones, "Guardar", self.evento_agregar_actualizar, "Primario.TButton").pack(side="left")
        self._boton(botones, "Eliminar", self.evento_eliminar, "Peligro.TButton").pack(side="left", padx=8)
        self._boton(botones, "Limpiar", self.limpiar_formulario).pack(side="left")

        cab = tk.Frame(panel, bg=C_CARD)
        cab.grid(row=5, column=0, sticky="ew", pady=(0, 6), **pad)
        self._boton(cab, "Exportar", self.evento_exportar_csv).pack(side="right")
        self._boton(cab, "Importar", self.evento_importar_csv).pack(side="right", padx=6)
        tk.Label(cab, text="Frecuencias", font=self.f(10, True), bg=C_CARD, fg=C_TEXTO).pack(side="left")
        self.lbl_conteo = tk.Label(cab, text="", font=self.f(9), bg=C_CARD, fg=C_SUAVE)
        self.lbl_conteo.pack(side="left", padx=6)

        cont = tk.Frame(panel, bg=C_CARD, highlightbackground=C_BORDE, highlightthickness=1)
        cont.grid(row=8, column=0, sticky="nsew", pady=(0, 14), **pad)
        self.tabla = ttk.Treeview(cont, columns=("actividad", "estudiantes", "porcentaje", "acumulado"),
                                  show="headings", style="Tabla.Treeview", height=6, selectmode="browse")
        for col, txt, ancho, ancla, estira in (("actividad", "Actividad", 150, "w", True), ("estudiantes", "Est.", 56, "center", False),
                                               ("porcentaje", "%", 66, "center", False), ("acumulado", "% Acum.", 76, "center", False)):
            self.tabla.heading(col, text=txt, anchor="w" if ancla == "w" else "center")
            self.tabla.column(col, width=ancho, minwidth=ancho if not estira else 110, anchor=ancla, stretch=estira)
        self.tabla.tag_configure("par", background="#FFFFFF")
        self.tabla.tag_configure("impar", background="#F8FAFC")
        sc = ttk.Scrollbar(cont, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sc.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
        self.tabla.bind("<<TreeviewSelect>>", self.evento_seleccionar_fila)
        self.tabla.bind("<Delete>", lambda _e: self.evento_eliminar())


    def _construir_panel_grafico(self, panel: tk.Frame) -> None:
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        top = tk.Frame(panel, bg=C_CARD)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        seg = tk.Frame(top, bg="#EEF2F7")
        seg.pack(side="left")
        for corto, completo in TIPOS_GRAFICO:
            ttk.Radiobutton(seg, text=corto, value=completo, variable=self.var_tipo_grafico,
                            style="Seg.Toolbutton", command=self.dibujar_grafica, cursor="hand2").pack(side="left")
        if MATPLOTLIB_DISPONIBLE:
            self._boton(top, "Guardar PNG", self.evento_exportar_png).pack(side="right")

        self.contenedor_lienzo = tk.Frame(panel, bg=C_CARD)
        self.contenedor_lienzo.grid(row=1, column=0, sticky="nsew", padx=8)
        if MATPLOTLIB_DISPONIBLE:
            self.figura = Figure(figsize=(7, 4.6), dpi=100, facecolor="#FFFFFF")
            self.canvas_mpl = FigureCanvasTkAgg(self.figura, master=self.contenedor_lienzo)
            self.canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
            self._id_redibujo = None
            self.contenedor_lienzo.bind("<Configure>", self._al_cambiar_tamano)
        else:
            self.canvas_tk = tk.Canvas(self.contenedor_lienzo, bg="#FFFFFF", highlightthickness=0)
            self.canvas_tk.pack(fill="both", expand=True)
            self.canvas_tk.bind("<Configure>", lambda e: self.dibujar_grafica())

        opciones = tk.Frame(panel, bg=C_CARD)
        opciones.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 6))
        ttk.Checkbutton(opciones, text="Mostrar etiquetas", variable=self.var_mostrar_etiquetas,
                        command=self.dibujar_grafica, style="Card.TCheckbutton").pack(side="left")
        ttk.Checkbutton(opciones, text="Ordenar de mayor a menor", variable=self.var_ordenar_desc,
                        command=self.actualizar_vista_completa, style="Card.TCheckbutton").pack(side="left", padx=16)

        insight = tk.Frame(panel, bg="#EFF6FF", highlightbackground="#BFDBFE", highlightthickness=1)
        insight.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
        tk.Label(insight, text="LECTURA RÁPIDA", font=self.f(8, True), bg="#EFF6FF", fg=C_PRIM_H).pack(anchor="w", padx=12, pady=(8, 0))
        self.lbl_resumen_dinamico = tk.Label(insight, text="", font=self.f(9), bg="#EFF6FF", fg="#1E293B", justify="left", anchor="w")
        self.lbl_resumen_dinamico.pack(fill="x", padx=12, pady=(2, 9))
        insight.bind("<Configure>", lambda e: self.lbl_resumen_dinamico.config(wraplength=max(200, e.width - 28)))

    # ------------------------------------------------------- texto de informes
    def _crear_texto_lectura(self, parent: tk.Widget) -> tk.Text:
        caja = tk.Frame(parent, bg=C_CARD, highlightbackground=C_BORDE, highlightthickness=1)
        caja.pack(fill="both", expand=True)
        sc = ttk.Scrollbar(caja, orient="vertical")
        sc.pack(side="right", fill="y")
        t = tk.Text(caja, wrap="word", font=self.f(10), bg=C_CARD, fg=C_TEXTO, padx=36, pady=22, relief="flat",
                    borderwidth=0, highlightthickness=0, yscrollcommand=sc.set, spacing2=3, cursor="arrow", insertwidth=0)
        t.pack(side="left", fill="both", expand=True)
        sc.config(command=t.yview)
        t.tag_configure("h1", font=self.f(13, True), foreground=C_PRIM_H, spacing1=18, spacing3=8)
        t.tag_configure("q", font=self.f(10, True), foreground=C_TEXTO, spacing1=12)
        t.tag_configure("a", lmargin1=22, lmargin2=22, foreground="#334155", spacing3=2)
        t.tag_configure("bold", font=self.f(10, True))
        t.tag_configure("destacado", font=self.f(10, True), background="#FEF3C7", foreground="#78350F")
        t.tag_configure("cita", font=(self.F, 10, "italic"), foreground="#475569", lmargin1=22, lmargin2=22)
        return t

    def _construir_tab_fase1(self) -> None:
        pag = self.tab_fase1
        marco = tk.Frame(pag, bg=C_BG)
        marco.pack(fill="both", expand=True, padx=20, pady=16)
        cab = tk.Frame(marco, bg=C_BG)
        cab.pack(fill="x", pady=(0, 10))
        izq = tk.Frame(cab, bg=C_BG)
        izq.pack(side="left")
        tk.Label(izq, text="Fase 1 · Situación inicial (40 %)", font=self.f(14, True), bg=C_BG, fg=C_TEXTO).pack(anchor="w")
        tk.Label(izq, text="Interpretación de la encuesta, reto de pensamiento crítico y conclusiones (en negrita lo solicitado).",
                 font=self.f(9), bg=C_BG, fg=C_SUAVE).pack(anchor="w")
        self._boton(cab, "Ver gráfico circular propuesto", self._ir_a_grafico_circular_oficial, "Primario.TButton").pack(side="right")
        self.txt_fase1 = self._crear_texto_lectura(marco)
        self._poblar_contenido_fase1()
        self.txt_fase1.config(state="disabled")

    def _poblar_contenido_fase1(self) -> None:
        t = self.txt_fase1
        t.insert("end", "1 · Respuestas a las preguntas de interpretación (100 estudiantes)\n", "h1")
        preguntas = [
            ("¿Cuál es la actividad más frecuente?", "Ver series o películas (28 estudiantes)."),
            ("¿Cuál es la actividad menos frecuente?", "Otras actividades (7 estudiantes)."),
            ("¿Cuántos estudiantes prefieren ver series o películas?", "28 estudiantes."),
            ("¿Cuántos estudiantes más prefieren escuchar música que leer?", "12 estudiantes más (22 prefieren escuchar música y 10 prefieren leer)."),
            ("¿Qué actividades son realizadas por más de 15 estudiantes?", "Ver series o películas (28), Escuchar música (22) y Practicar deporte (18)."),
            ("¿Qué porcentaje de los estudiantes practica deporte?", "El 18 % (18 de 100 estudiantes encuestados)."),
            ("¿Qué diferencias importantes observas entre las actividades?", "Las actividades de entretenimiento pasivo y digital (series y música) concentran el 50 % de la muestra, superando ampliamente a las actividades físicas (18 %) y de lectura (10 %)."),
            ("¿Qué conclusión general puedes obtener a partir de los datos?", "La mayoría de la muestra prefiere consumir entretenimiento audiovisual y musical en su tiempo libre, aunque un 28 % mantiene hábitos activos de deporte y lectura."),
            ("¿Qué información no podemos conocer a partir de este gráfico?", "No podemos conocer el tiempo diario dedicado a cada actividad, si realizan varias simultáneamente, ni las características demográficas de los estudiantes."),
            ("Si tuvieras que presentar estos resultados a la institución, ¿qué otro tipo de gráfico utilizarías y por qué?", "Un gráfico circular (o de pastel) y un diagrama de Pareto. Como la muestra es de 100 estudiantes, cada estudiante equivale al 1 %, lo que permite ver de inmediato la proporción exacta de cada categoría respecto al total institucional."),
        ]
        for i, (preg, resp) in enumerate(preguntas, start=1):
            t.insert("end", f"{i}. {preg}\n", "q")
            t.insert("end", resp + "\n", "a")

        t.insert("end", "\n2 · Reto de pensamiento crítico\n", "h1")
        t.insert("end", "“El gráfico muestra que ver series o películas es la actividad más popular. ¿Podemos concluir que los estudiantes prefieren pasar todo su tiempo libre frente a una pantalla?”\n", "cita")
        t.insert("end", "\nNo, no se puede concluir esto de forma absoluta. Basados únicamente en los datos disponibles, aunque “Ver series o películas” (28) y “Jugar videojuegos” (15) implican el uso de pantallas (43 estudiantes, es decir, el 43 %), la mayoría de la población encuestada (57 estudiantes, el 57 %) prefiere actividades principales que no son frente a una pantalla: “Escuchar música” (22), “Practicar deporte” (18), “Leer” (10) y “Otras actividades” (7). Además, los datos reflejan la actividad preferida, pero no indican que los estudiantes dediquen todo su tiempo libre exclusivamente a ella.\n", "a")

        t.insert("end", "\n3 · Producto final: conclusiones\n", "h1")
        t.insert("end", "Al analizar los resultados de la encuesta, podemos extraer como ")
        t.insert("end", "observación sobre el dato más alto que la actividad preferida por la mayoría es “Ver series o películas”, reuniendo a 28 de los 100 estudiantes encuestados.", "destacado")
        t.insert("end", "\n\nPor otro lado, al realizar ")
        t.insert("end", "una comparación entre dos categorías, se hace evidente que el número de estudiantes interesados en “Escuchar música” (22 estudiantes) es superior y representa más del doble respecto a los que prefieren “Leer” (10 estudiantes).", "destacado")
        t.insert("end", "\n\nEn términos generales, ")
        t.insert("end", "la tendencia o patrón identificado demuestra una inclinación muy fuerte hacia el entretenimiento pasivo y el consumo de medios, los cuales concentran la atención de la mayor parte de la muestra, marginando a un segundo plano las actividades físicas.", "destacado")
        t.insert("end", "\n\nFinalmente, y como ")
        t.insert("end", "conclusión sustentada en los datos, es posible afirmar que si bien los estudiantes se ven atraídos por el entorno digital (43 % entre series y videojuegos), existe una diversidad de intereses palpable en el 57 % que elige música, deporte, lectura y otras actividades, demostrando que no todo el tiempo libre estudiantil está sujeto a una pantalla.", "destacado")
        t.insert("end", "\n")

    def _construir_tab_arquitectura(self) -> None:
        pag = self.tab_arquitectura
        marco = tk.Frame(pag, bg=C_BG)
        marco.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(marco, text="Guía, pruebas y ejecutable portable", font=self.f(14, True), bg=C_BG, fg=C_TEXTO).pack(anchor="w")
        tk.Label(marco, text="Evidencia de funcionamiento del software y respuesta a las preguntas orientadoras.",
                 font=self.f(9), bg=C_BG, fg=C_SUAVE).pack(anchor="w", pady=(0, 10))

        fila = tk.Frame(marco, bg=C_BG)
        fila.pack(fill="x", pady=(0, 12))
        fila.grid_columnconfigure(0, weight=1, uniform="acc")
        fila.grid_columnconfigure(1, weight=1, uniform="acc")

        # tarjeta pruebas
        c1 = self._tarjeta(fila)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Label(c1, text="Pruebas automatizadas", font=self.f(11, True), bg=C_CARD, fg=C_TEXTO).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(c1, text="Verifica los 100 estudiantes, las validaciones, la protección del dataset oficial y la importación/exportación CSV.",
                 font=self.f(9), bg=C_CARD, fg=C_SUAVE, justify="left", wraplength=420).pack(anchor="w", padx=16)
        self._boton(c1, "Ejecutar pruebas", self.evento_ejecutar_autoprueba, "Exito.TButton").pack(anchor="w", padx=16, pady=(10, 6))
        self.lbl_resultado_pruebas = tk.Label(c1, text="Aún no se han ejecutado.", font=self.f(10, True), bg=C_CARD, fg=C_SUAVE)
        self.lbl_resultado_pruebas.pack(anchor="w", padx=16)
        fuente_mono = "Consolas" if "Consolas" in set(tkfont.families(self.root)) else "Courier"
        self.txt_detalle_pruebas = tk.Text(c1, height=6, font=(fuente_mono, 9), bg="#F8FAFC", fg="#334155", relief="flat",
                                           borderwidth=0, highlightthickness=1, highlightbackground=C_BORDE, padx=8, pady=6, state="disabled")
        self.txt_detalle_pruebas.pack(fill="x", padx=16, pady=(6, 14))

        # tarjeta exe
        c2 = self._tarjeta(fila)
        c2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        tk.Label(c2, text="Ejecutable portable (.exe)", font=self.f(11, True), bg=C_CARD, fg=C_TEXTO).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(c2, text="Genera un único archivo AnaliticaBI_UMB.exe que corre en otro equipo sin instalar Python (requiere PyInstaller en este equipo).",
                 font=self.f(9), bg=C_CARD, fg=C_SUAVE, justify="left", wraplength=420).pack(anchor="w", padx=16)
        self.btn_exe = self._boton(c2, "Generar .exe", self.evento_compilar_exe_desde_gui, "Primario.TButton")
        self.btn_exe.pack(anchor="w", padx=16, pady=(10, 6))
        self.lbl_exe = tk.Label(c2, text="", font=self.f(9), bg=C_CARD, fg=C_SUAVE, justify="left", wraplength=420)
        self.lbl_exe.pack(anchor="w", padx=16, pady=(0, 14))
        if getattr(sys, "frozen", False):
            self.btn_exe.state(["disabled"])
            self.lbl_exe.config(text="Ya estás usando la versión portable (.exe).")

        t = self._crear_texto_lectura(marco)
        t.insert("end", "Preguntas orientadoras de la Guía 9\n", "h1")
        qa = [
            ("¿Qué tipo de datos serán ingresados al software y cuál es su propósito?",
             "Datos categóricos (actividades de tiempo libre) y numéricos enteros positivos (frecuencias de estudiantes) para estructurar tablas de frecuencia y automatizar diagramas estadísticos."),
            ("¿Cómo se garantizará que los datos ingresados sean completos, válidos y consistentes?",
             "Mediante GestorDatosBI.validar_registro(): exige campos no vacíos, rechaza texto en el número, decimales, ceros y negativos, y protege el dataset original de 100 estudiantes contra sobrescritura accidental."),
            ("¿Por qué se seleccionó cada tipo de visualización?",
             "Barras verticales: comparan magnitudes absolutas. Circular: muestra la proporción exacta sobre el 100 %. Barras horizontales: facilitan el ranking y la lectura de nombres largos. Pareto: combina frecuencia y porcentaje acumulado (regla 80/20)."),
            ("¿Puede el software ejecutarse en otro equipo sin una configuración compleja?",
             "Sí. Funciona sin conexión a internet y puede empaquetarse en un único AnaliticaBI_UMB.exe portable; los datos se guardan en una carpeta “datos” junto al ejecutable."),
            ("¿Qué pruebas se realizaron para verificar el funcionamiento?",
             "Pruebas unitarias automáticas (botón “Ejecutar pruebas”) sobre la muestra de 100 estudiantes, las validaciones, la creación de datasets sin alterar el original y el ciclo importar/exportar CSV."),
        ]
        for i, (q, a) in enumerate(qa, start=1):
            t.insert("end", f"{i}. {q}\n", "q")
            t.insert("end", a + "\n", "a")
        t.config(state="disabled")

    # -------------------------------------------------------------- actualizar
    def _actualizar_estado_edicion(self) -> None:
        oficial = self.gestor.dataset_actual == NOMBRE_DATASET_OFICIAL
        if oficial:
            self.lbl_badge.config(text="OFICIAL", bg=C_AMBAR_BG, fg=C_AMBAR)
            self.aviso.grid()
            if self.var_permitir_edicion_oficial.get():
                self.lbl_aviso.config(text="Edición del dataset oficial desbloqueada: se pierde la trazabilidad respecto a los datos originales de la guía.")
            else:
                self.lbl_aviso.config(text="Dataset oficial protegido para mantener la trazabilidad de la Guía 9. Crea una copia para agregar o modificar datos.")
        else:
            self.lbl_badge.config(text="EDITABLE", bg="#D1FAE5", fg="#065F46")
            self.aviso.grid_remove()

    def actualizar_vista_completa(self) -> None:
        self.combo_datasets["values"] = list(self.gestor.datasets.keys())
        self.var_dataset.set(self.gestor.dataset_actual)
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        filas = self.gestor.obtener_registros_enriquecidos(ordenar_desc=self.var_ordenar_desc.get())
        for i, fila in enumerate(filas):
            self.tabla.insert("", "end", tags=("par" if i % 2 == 0 else "impar",),
                              values=(fila["actividad"], int(fila["estudiantes"]), f"{fila['porcentaje']:.1f}%", f"{fila['porcentaje_acumulado']:.1f}%"))
        self.lbl_conteo.config(text=f"({len(filas)})")

        s = self.gestor.calcular_estadisticas()
        self.kpi_total[0].config(text=f"{s['total_estudiantes']}")
        self.kpi_total[1].config(text=f"estudiantes en {s['num_categorias']} categorías")
        self.kpi_mayor[0].config(text=s["actividad_mayor"])
        self.kpi_mayor[1].config(text=f"{s['valor_mayor']} estudiantes · {s['porcentaje_mayor']:.1f} %")
        self.kpi_menor[0].config(text=s["actividad_menor"])
        self.kpi_menor[1].config(text=f"{s['valor_menor']} estudiantes · {s['porcentaje_menor']:.1f} %")
        self.kpi_promedio[0].config(text=f"{s['promedio']:.2f}")
        self.kpi_promedio[1].config(text=f"por categoría · rango {s['rango']}")

        if s["num_categorias"]:
            mas15 = ", ".join(s["actividades_mas_de_15"]) if s["actividades_mas_de_15"] else "ninguna"
            texto = (f"“{s['actividad_mayor']}” lidera con {s['valor_mayor']} estudiantes ({s['porcentaje_mayor']:.1f} %); "
                     f"la menos frecuente es “{s['actividad_menor']}” con {s['valor_menor']} ({s['porcentaje_menor']:.1f} %). "
                     f"Actividades con más de 15 estudiantes: {mas15}.")
        else:
            texto = "Este conjunto de datos está vacío. Agrega registros en el panel izquierdo para generar el gráfico."
        self.lbl_resumen_dinamico.config(text=texto)
        self._actualizar_estado_edicion()
        self.dibujar_grafica()

    # ---------------------------------------------------------------- gráficos
    def dibujar_grafica(self) -> None:
        if MATPLOTLIB_DISPONIBLE:
            self._dibujar_con_matplotlib()
        else:
            self._dibujar_con_canvas_nativo()

    def _al_cambiar_tamano(self, _event=None) -> None:
        if self._id_redibujo:
            self.root.after_cancel(self._id_redibujo)
        self._id_redibujo = self.root.after(180, self.dibujar_grafica)

    @staticmethod
    def _envolver(texto, ancho: int = 14) -> str:
        return textwrap.fill(str(texto), ancho)

    def _estilo_ejes(self, ax, grid: str = "y") -> None:
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color("#CBD5E1")
        ax.tick_params(colors=C_SUAVE, labelsize=9, length=0)
        ax.set_facecolor("#FFFFFF")
        ax.grid(axis=grid, color="#E8EDF3", linewidth=1)
        ax.set_axisbelow(True)

    def _encabezado_figura(self, titulo: str, subtitulo: str) -> None:
        alto = max(self.figura.get_figheight(), 1)
        self.figura.text(0.035, 1 - 0.12 / alto, titulo, fontsize=14, fontweight="bold", color=C_TEXTO, va="top", ha="left")
        self.figura.text(0.035, 1 - 0.48 / alto, subtitulo, fontsize=9.5, color=C_SUAVE, va="top", ha="left")

    def _tope(self) -> float:
        """Fracción de la figura disponible bajo el título (se mide en pulgadas para que no se pise en ventanas bajas)."""
        return 1 - 0.85 / max(self.figura.get_figheight(), 1)

    def _dibujar_con_matplotlib(self) -> None:
        self.figura.clear()
        filas = self.gestor.obtener_registros_enriquecidos(ordenar_desc=self.var_ordenar_desc.get())
        if not filas or sum(f["estudiantes"] for f in filas) == 0:
            self.figura.text(0.5, 0.5, "Conjunto de datos vacío\nAgrega registros para graficar automáticamente",
                             ha="center", va="center", fontsize=12, color=C_SUAVE)
            self.canvas_mpl.draw_idle()
            return

        n = len(filas)
        nombres = [f["actividad"] for f in filas]
        valores = [int(f["estudiantes"]) for f in filas]
        pcts = [f["porcentaje"] for f in filas]
        total = sum(valores)
        etiquetas = self.var_mostrar_etiquetas.get()
        tipo = self.var_tipo_grafico.get()
        subtitulo = f"{self.gestor.dataset_actual}  ·  N = {total}"
        i_max = valores.index(max(valores))
        col_barras = [C_PRIM if i == i_max else "#9DB8F5" for i in range(n)]
        rot = 0 if n <= 7 else 35
        ha = "center" if rot == 0 else "right"
        colores = [PALETA_COLORES[i % len(PALETA_COLORES)] for i in range(n)]

        if tipo.startswith("Barras Verticales"):
            self._encabezado_figura("Actividades en el tiempo libre", subtitulo)
            ax = self.figura.add_subplot(111)
            self._estilo_ejes(ax, "y")
            barras = ax.bar(range(n), valores, color=col_barras, width=0.62)
            ax.set_xticks(range(n))
            ax.set_xticklabels([self._envolver(a) for a in nombres], rotation=rot, ha=ha)
            ax.set_ylim(0, max(valores) * 1.22)
            ax.set_ylabel("Número de estudiantes", color=C_SUAVE, fontsize=9.5)
            if etiquetas:
                for b, p in zip(barras, pcts):
                    ax.annotate(f"{int(b.get_height())}  ({p:.1f} %)", (b.get_x() + b.get_width() / 2, b.get_height()),
                                xytext=(0, 5), textcoords="offset points", ha="center", va="bottom",
                                fontsize=9, fontweight="bold", color=C_TEXTO)
            self.figura.tight_layout(rect=(0, 0.02, 1, self._tope()))

        elif tipo.startswith("Gráfico Circular"):
            self._encabezado_figura("Distribución porcentual", subtitulo)
            ax = self.figura.add_subplot(111)
            ancho_anillo = 0.38
            cuñas, _ = ax.pie(valores, colors=colores, startangle=90, counterclock=False,
                              wedgeprops=dict(width=ancho_anillo, edgecolor="#FFFFFF", linewidth=2))
            ax.text(0, 0.06, f"{total}", ha="center", va="center", fontsize=22, fontweight="bold", color=C_TEXTO)
            ax.text(0, -0.14, "estudiantes", ha="center", va="center", fontsize=9.5, color=C_SUAVE)
            if etiquetas:
                import math
                for w, p in zip(cuñas, pcts):
                    if p >= 6:
                        ang = math.radians((w.theta1 + w.theta2) / 2)
                        r = 1 - ancho_anillo / 2
                        ax.text(r * math.cos(ang), r * math.sin(ang), f"{p:.0f}%", ha="center", va="center",
                                color="#FFFFFF", fontsize=9, fontweight="bold")
            leyenda = [Patch(facecolor=colores[i], label=f"{nombres[i]}  —  {valores[i]}  ({pcts[i]:.1f} %)") for i in range(n)]
            ax.legend(handles=leyenda, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9.5, labelcolor=C_TEXTO)
            ax.set_aspect("equal")
            self.figura.subplots_adjust(left=0.02, right=0.60, top=self._tope() - 0.02, bottom=0.04)

        elif tipo.startswith("Barras Horizontales"):
            self._encabezado_figura("Comparativo por actividad", subtitulo)
            ax = self.figura.add_subplot(111)
            self._estilo_ejes(ax, "x")
            ax.grid(axis="y", visible=False)
            barras = ax.barh(range(n), valores, color=col_barras, height=0.6)
            ax.set_yticks(range(n))
            ax.set_yticklabels([self._envolver(a, 24) for a in nombres])
            ax.invert_yaxis()
            ax.set_xlim(0, max(valores) * 1.28)
            ax.set_xlabel("Número de estudiantes", color=C_SUAVE, fontsize=9.5)
            if etiquetas:
                for b, p in zip(barras, pcts):
                    ax.annotate(f"{int(b.get_width())}  ({p:.1f} %)", (b.get_width(), b.get_y() + b.get_height() / 2),
                                xytext=(6, 0), textcoords="offset points", va="center", ha="left",
                                fontsize=9, fontweight="bold", color=C_TEXTO)
            self.figura.tight_layout(rect=(0, 0.02, 1, self._tope()))

        else:
            fp = self.gestor.obtener_registros_enriquecidos(ordenar_desc=True)
            np_ = len(fp)
            act_p = [f["actividad"] for f in fp]
            est_p = [int(f["estudiantes"]) for f in fp]
            acum_p = [f["porcentaje_acumulado"] for f in fp]
            self._encabezado_figura("Diagrama de Pareto (regla 80/20)", subtitulo)
            ax1 = self.figura.add_subplot(111)
            self._estilo_ejes(ax1, "y")
            ax2 = ax1.twinx()
            ax1.bar(range(np_), est_p, color="#3B82F6", width=0.6)
            ax2.plot(range(np_), acum_p, color="#F97316", marker="o", markersize=6, linewidth=2.4)
            ax2.axhline(80, color="#F59E0B", linestyle="--", linewidth=1.2)
            ax2.text(np_ - 0.45, 81.5, "80 %", color="#B45309", fontsize=8.5, fontweight="bold", ha="right")
            ax2.set_ylim(0, 110)
            ax2.yaxis.set_major_formatter(PercentFormatter(100))
            ax2.tick_params(colors=C_SUAVE, labelsize=9, length=0)
            for lado in ("top", "right", "left", "bottom"):
                ax2.spines[lado].set_visible(False)
            ax1.set_xticks(range(np_))
            ax1.set_xticklabels([self._envolver(a) for a in act_p], rotation=rot, ha=ha)
            ax1.set_ylim(0, max(est_p) * 1.22)
            ax1.set_ylabel("Número de estudiantes", color=C_SUAVE, fontsize=9.5)
            if etiquetas:
                for i, v in enumerate(acum_p):
                    ax2.annotate(f"{v:.0f}%", (i, v), xytext=(0, 9), textcoords="offset points", ha="center",
                                 fontsize=8.5, fontweight="bold", color="#C2410C",
                                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
            self.figura.tight_layout(rect=(0, 0.02, 1, self._tope()))

        self.canvas_mpl.draw_idle()

    def _dibujar_con_canvas_nativo(self) -> None:
        c = self.canvas_tk
        c.delete("all")
        w = max(c.winfo_width(), 520)
        h = max(c.winfo_height(), 360)
        filas = self.gestor.obtener_registros_enriquecidos(ordenar_desc=self.var_ordenar_desc.get())
        if not filas:
            c.create_text(w // 2, h // 2, text="Sin datos para graficar", font=self.f(12), fill=C_SUAVE)
            return
        margen_izq, margen_der, margen_sup, margen_inf = 60, 30, 55, 70
        c.create_text(24, 24, anchor="w", text="Actividades realizadas en el tiempo libre", font=self.f(13, True), fill=C_TEXTO)
        c.create_text(24, 46, anchor="w", text=f"{self.gestor.dataset_actual}", font=self.f(9), fill=C_SUAVE)
        max_val = max(f["estudiantes"] for f in filas) or 1
        n = len(filas)
        paso = (w - margen_izq - margen_der) / n
        alto_util = h - margen_sup - margen_inf
        for i, fila in enumerate(filas):
            x0 = margen_izq + i * paso + paso * 0.18
            x1 = margen_izq + (i + 1) * paso - paso * 0.18
            y1 = h - margen_inf
            y0 = y1 - (fila["estudiantes"] / max_val) * (alto_util - 20)
            c.create_rectangle(x0, y0, x1, y1, fill=C_PRIM, outline="")
            c.create_text((x0 + x1) / 2, y0 - 10, text=f"{fila['estudiantes']} ({fila['porcentaje']:.0f}%)", font=self.f(8, True), fill=C_TEXTO)
            c.create_text((x0 + x1) / 2, y1 + 18, text=fila["actividad"][:16], font=self.f(8), fill=C_SUAVE)

    # ------------------------------------------------------------------ eventos
    def _mensaje_form(self, texto: str, tipo: str = "error") -> None:
        self.lbl_form_msg.config(text=texto, fg=C_PELIGRO if tipo == "error" else C_OK)

    def limpiar_formulario(self) -> None:
        self.var_actividad.set("")
        self.var_estudiantes.set("")
        self.lbl_form_msg.config(text="")
        self.tabla.selection_remove(self.tabla.selection())

    def evento_seleccionar_fila(self, _event=None) -> None:
        sel = self.tabla.selection()
        if not sel:
            return
        valores = self.tabla.item(sel[0], "values")
        if valores:
            self.var_actividad.set(valores[0])
            self.var_estudiantes.set(valores[1])
            self.lbl_form_msg.config(text="")

    def evento_agregar_actualizar(self) -> None:
        ok, msg = self.gestor.agregar_o_actualizar_registro(
            self.var_actividad.get(), self.var_estudiantes.get(),
            permitir_edicion_oficial=self.var_permitir_edicion_oficial.get())
        if not ok:
            self._mensaje_form(msg, "error")
            return
        self.limpiar_formulario()
        self.actualizar_vista_completa()
        self._mensaje_form(msg, "ok")
        self._estado(msg)
        self.entry_actividad.focus_set()

    def evento_eliminar(self) -> None:
        act = self.var_actividad.get().strip()
        if not act:
            self._mensaje_form("Selecciona una fila de la tabla para eliminarla.", "error")
            return
        if not messagebox.askyesno("Confirmar eliminación", f"¿Desea eliminar la actividad “{act}”?"):
            return
        ok, msg = self.gestor.eliminar_registro(act, permitir_edicion_oficial=self.var_permitir_edicion_oficial.get())
        if not ok:
            self._mensaje_form(msg, "error")
            return
        self.limpiar_formulario()
        self.actualizar_vista_completa()
        self._estado(msg)

    def evento_cambiar_dataset(self, _event=None) -> None:
        sel = self.var_dataset.get()
        if sel in self.gestor.datasets:
            self.gestor.dataset_actual = sel
            self.gestor.guardar_json()
            self.limpiar_formulario()
            self.actualizar_vista_completa()

    def evento_crear_dataset(self, copiar: bool = False) -> None:
        titulo = "Crear copia editable" if copiar else "Crear dataset vacío"
        sugerencia = "Simulación Bienestar UMB" if copiar else "Nueva Encuesta"
        nombre = simpledialog.askstring(titulo, "Nombre para el nuevo conjunto de datos:", initialvalue=sugerencia, parent=self.root)
        if nombre is None:
            return
        ok, msg = self.gestor.crear_dataset(nombre, copiar_actual=copiar)
        if not ok:
            messagebox.showwarning("Atención", msg)
            return
        self.limpiar_formulario()
        self.actualizar_vista_completa()
        self._estado(msg)
        self.entry_actividad.focus_set()

    def evento_eliminar_dataset(self) -> None:
        actual = self.gestor.dataset_actual
        if actual == NOMBRE_DATASET_OFICIAL:
            messagebox.showwarning("Dataset protegido", "El dataset oficial de la Guía 9 no puede eliminarse.")
            return
        if messagebox.askyesno("Eliminar dataset", f"¿Eliminar permanentemente “{actual}”?"):
            ok, msg = self.gestor.eliminar_dataset(actual)
            self.actualizar_vista_completa()
            self._estado(msg, "ok" if ok else "error")

    def evento_restaurar_oficial(self) -> None:
        self.gestor.restaurar_dataset_oficial()
        self.limpiar_formulario()
        self.actualizar_vista_completa()
        self._estado("Se restauraron los datos originales de los 100 estudiantes (Guía 9).")

    def evento_importar_csv(self) -> None:
        ruta = filedialog.askopenfilename(title="Seleccionar archivo CSV", filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")])
        if not ruta:
            return
        ok, msg = self.gestor.importar_csv(ruta)
        if not ok:
            messagebox.showerror("Error al importar", msg)
            return
        self.actualizar_vista_completa()
        self._estado(msg)

    def evento_exportar_csv(self) -> None:
        ruta = filedialog.asksaveasfilename(title="Exportar a CSV", defaultextension=".csv", initialfile="resultados_encuesta_bi.csv", filetypes=[("Archivo CSV", "*.csv")])
        if not ruta:
            return
        ok, msg = self.gestor.exportar_csv(ruta)
        if ok:
            self._estado(msg)
        else:
            messagebox.showerror("Error", msg)

    def evento_exportar_png(self) -> None:
        if not MATPLOTLIB_DISPONIBLE:
            return
        ruta = filedialog.asksaveasfilename(title="Guardar gráfico como PNG", defaultextension=".png", initialfile="grafica_business_analytics.png", filetypes=[("Imagen PNG", "*.png")])
        if not ruta:
            return
        try:
            self.figura.savefig(ruta, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
            self._estado(f"Gráfico guardado en {ruta}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _ir_a_grafico_circular_oficial(self) -> None:
        self.gestor.dataset_actual = NOMBRE_DATASET_OFICIAL
        self.var_tipo_grafico.set("Gráfico Circular / Pastel (Porcentajes)")
        self.actualizar_vista_completa()
        self.mostrar_pestana("dashboard")

    def evento_ejecutar_autoprueba(self) -> None:
        flujo = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(PruebasAutomatizadasBI)
        res = unittest.TextTestRunner(stream=flujo, verbosity=2).run(suite)
        aprobadas = res.testsRun - len(res.failures) - len(res.errors)
        ok = res.wasSuccessful()
        self.lbl_resultado_pruebas.config(
            text=f"{'✔ APROBADO' if ok else '✘ REVISAR'} · {aprobadas}/{res.testsRun} pruebas correctas · {len(res.failures)} fallos · {len(res.errors)} errores",
            fg=C_OK if ok else C_PELIGRO)
        self.txt_detalle_pruebas.config(state="normal")
        self.txt_detalle_pruebas.delete("1.0", "end")
        self.txt_detalle_pruebas.insert("end", flujo.getvalue().strip())
        self.txt_detalle_pruebas.config(state="disabled")
        self._estado("Pruebas ejecutadas.", "ok" if ok else "error")

    def evento_compilar_exe_desde_gui(self) -> None:
        if getattr(sys, "frozen", False):
            return
        archivo = os.path.abspath(__file__)
        carpeta = os.path.dirname(archivo)
        self.btn_exe.state(["disabled"])
        self.lbl_exe.config(text="Compilando… puede tardar entre 1 y 3 minutos. Puedes seguir usando la aplicación.", fg=C_SUAVE)
        self._resultado_compilacion = None

        def tarea():
            try:
                cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
                       "--name", "AnaliticaBI_UMB", "--hidden-import", "pandas",
                       "--hidden-import", "matplotlib.backends.backend_tkagg", archivo]
                res = subprocess.run(cmd, cwd=carpeta, capture_output=True, text=True,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                exe = os.path.join(carpeta, "dist", "AnaliticaBI_UMB.exe")
                if res.returncode == 0 and os.path.exists(exe):
                    destino = os.path.join(carpeta, "AnaliticaBI_UMB.exe")
                    shutil.copy2(exe, destino)
                    self._resultado_compilacion = (True, destino)
                else:
                    detalle = (res.stderr or res.stdout or "").strip().splitlines()
                    self._resultado_compilacion = (False, detalle[-1] if detalle else "PyInstaller no está instalado (pip install pyinstaller).")
            except Exception as e:
                self._resultado_compilacion = (False, str(e))

        threading.Thread(target=tarea, daemon=True).start()
        self.root.after(700, self._revisar_compilacion)

    def _revisar_compilacion(self) -> None:
        if self._resultado_compilacion is None:
            self.root.after(700, self._revisar_compilacion)
            return
        ok, detalle = self._resultado_compilacion
        self.btn_exe.state(["!disabled"])
        if ok:
            self.lbl_exe.config(text=f"✔ Ejecutable generado:\n{detalle}", fg=C_OK)
            self._estado("Ejecutable portable generado correctamente.")
        else:
            self.lbl_exe.config(text=f"✘ No se pudo compilar: {detalle}", fg=C_PELIGRO)
            self._estado("No se pudo generar el ejecutable.", "error")



class PruebasAutomatizadasBI(unittest.TestCase):
    def setUp(self):
        self.ruta_test = os.path.join(obtener_ruta_base(), "datos", "test_temp.json")
        if os.path.exists(self.ruta_test):
            os.remove(self.ruta_test)
        self.gestor = GestorDatosBI(ruta_almacenamiento=self.ruta_test)

    def tearDown(self):
        if os.path.exists(self.ruta_test):
            try:
                os.remove(self.ruta_test)
            except Exception:
                pass

    def test_01_encuesta_100_estudiantes(self):
        stats = self.gestor.calcular_estadisticas()
        self.assertEqual(stats["total_estudiantes"], 100)
        self.assertEqual(stats["actividad_mayor"], "Ver series o películas")
        self.assertEqual(stats["valor_mayor"], 28)
        self.assertEqual(stats["actividad_menor"], "Otras actividades")
        self.assertEqual(stats["valor_menor"], 7)

    def test_02_validaciones(self):
        self.assertFalse(self.gestor.validar_registro("", "10")[0])
        self.assertFalse(self.gestor.validar_registro("Cine", "abc")[0])
        self.assertFalse(self.gestor.validar_registro("Cine", "-4")[0])
        self.assertFalse(self.gestor.validar_registro("Cine", "12.5")[0])
        self.assertTrue(self.gestor.validar_registro("Teatro", "15")[0])

    def test_03_creacion_dataset_sin_modificar_oficial(self):
        self.assertFalse(self.gestor.agregar_o_actualizar_registro("X", "10", permitir_edicion_oficial=False)[0])
        self.assertTrue(self.gestor.crear_dataset("Nuevo Test", copiar_actual=False)[0])
        self.gestor.agregar_o_actualizar_registro("Deporte", "25")
        self.assertEqual(self.gestor.calcular_estadisticas()["total_estudiantes"], 25)
        self.gestor.dataset_actual = NOMBRE_DATASET_OFICIAL
        self.assertEqual(self.gestor.calcular_estadisticas()["total_estudiantes"], 100)

    def test_04_importar_exportar_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "prueba.csv")
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                f.write("actividad,estudiantes\nCine,30\nTeatro,20\n")
            self.assertTrue(self.gestor.importar_csv(ruta)[0])
            self.assertEqual(self.gestor.calcular_estadisticas()["total_estudiantes"], 50)
            destino = os.path.join(tmp, "salida.csv")
            self.assertTrue(self.gestor.exportar_csv(destino)[0])
            self.assertTrue(os.path.exists(destino))
            malo = os.path.join(tmp, "malo.csv")
            with open(malo, "w", newline="", encoding="utf-8") as f:
                f.write("actividad,estudiantes\nCine,abc\n")
            self.assertFalse(self.gestor.importar_csv(malo)[0])

    def test_05_porcentajes_coherentes(self):
        filas = self.gestor.obtener_registros_enriquecidos()
        self.assertAlmostEqual(sum(f["porcentaje"] for f in filas), 100.0, places=1)
        self.assertEqual(filas[-1]["porcentaje_acumulado"], 100.0)


def _activar_nitidez_windows() -> None:
    """Evita el texto borroso en pantallas con escalado (125 %, 150 %...) en Windows."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    if "--test" in sys.argv:
        sys.argv = [sys.argv[0]]
        unittest.main(verbosity=2)
        return
    _activar_nitidez_windows()
    root = tk.Tk()
    app = AplicacionAnaliticaBI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
