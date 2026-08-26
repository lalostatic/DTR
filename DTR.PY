import os
import sys
import json
import shutil
import subprocess
import threading
import tkinter as tk

from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import time

from PIL import Image, ImageTk


# ============================================================
# DTR v4
# REMOTE TEMP CLEANER
# ============================================================

APP_NAME = "DTR"

NETWORK_PREFIX = "192.168.0."
IP_START = 1
IP_END = 254

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "dtr_history.json"


# ============================================================
# COLORES
# ============================================================

BG = "#070b10"
PANEL = "#0d131b"
PANEL2 = "#111a24"
BORDER = "#1e2a36"

TEXT = "#e6edf3"
MUTED = "#778596"

BLUE = "#2383ff"
CYAN = "#22d3ee"
GREEN = "#35d07f"
YELLOW = "#f0b429"
RED = "#ff5570"
PURPLE = "#9b7cff"


# ============================================================
# RECURSOS
# ============================================================

def resource_path(filename):
    """
    Obtiene la ruta de los recursos.

    Funciona tanto ejecutando el archivo .py como
    ejecutando un .exe creado con PyInstaller.
    """

    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).resolve().parent

    return base_path / filename


def load_logo(filename="DTR.png", size=(350, 350)):
    """
    Carga el logo manteniendo sus proporciones.
    """

    logo_path = resource_path(filename)

    if not logo_path.exists():
        return None

    try:
        image = Image.open(logo_path)

        image.thumbnail(
            size,
            Image.LANCZOS
        )

        return ImageTk.PhotoImage(image)

    except Exception as error:
        print(
            f"Error cargando logo: {error}"
        )

        return None


# ============================================================
# HISTORIAL
# ============================================================

def default_history():
    return {
        "completed": {},
        "pending": {}
    }


def load_history():

    if not HISTORY_FILE.exists():
        return default_history()

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return default_history()

        data.setdefault(
            "completed",
            {}
        )

        data.setdefault(
            "pending",
            {}
        )

        return data

    except Exception:
        return default_history()


def save_history(data):

    try:

        temp_file = HISTORY_FILE.with_suffix(
            ".tmp"
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        os.replace(
            temp_file,
            HISTORY_FILE
        )

    except Exception as error:

        print(
            f"History error: {error}"
        )


# ============================================================
# APLICACIÓN
# ============================================================

class DTRApp:

    def __init__(self, root):

        self.root = root

        # ----------------------------------------------------
        # VENTANA
        # ----------------------------------------------------

        self.root.title(
            "DTR"
        )

        self.root.geometry(
            "1080x700"
        )

        self.root.minsize(
            950,
            620
        )

        self.root.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # ICONO
        # ----------------------------------------------------

        icon_path = resource_path(
            "DTR.ico"
        )

        if icon_path.exists():

            try:

                self.root.iconbitmap(
                    str(icon_path)
                )

            except Exception as error:

                print(
                    f"No se pudo cargar el icono: {error}"
                )

        # ----------------------------------------------------
        # OCULTAR VENTANA PRINCIPAL
        # ----------------------------------------------------

        self.root.withdraw()

        # ----------------------------------------------------
        # VARIABLES DE ESTADO
        # ----------------------------------------------------

        self.history = load_history()

        self.scanning = False
        self.cleaning = False
        self.stop_requested = False

        self.active_ips = []

        self.total_devices = 0
        self.processed_devices = 0

        self.deleted_files = 0
        self.skipped_files = 0

        self.start_time = None

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.create_styles()

        self.create_interface()

        self.refresh_pending()

        self.update_clock()

        self.log(
            "DTR v4 iniciado."
        )

        self.log(
            "Red configurada: 192.168.0.0/24"
        )

        # ----------------------------------------------------
        # SPLASH
        # ----------------------------------------------------

        self.show_splash()

    # ========================================================
    # PANTALLA DE BIENVENIDA
    # ========================================================

    def show_splash(self):

        splash = tk.Toplevel(
            self.root
        )

        splash.overrideredirect(
            True
        )

        splash.configure(
            bg=BG
        )

        width = 420
        height = 320

        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()

        x = (
            screen_width - width
        ) // 2

        y = (
            screen_height - height
        ) // 2

        splash.geometry(
            f"{width}x{height}+{x}+{y}"
        )

        # ----------------------------------------------------
        # CONTENEDOR
        # ----------------------------------------------------

        container = tk.Frame(
            splash,
            bg=BG
        )

        container.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        logo = load_logo(
            "DTR.png",
            (200, 200)
        )

        if logo:

            logo_label = tk.Label(
                container,
                image=logo,
                bg=BG
            )

            splash.logo_image = logo

            logo_label.pack(
                pady=(20, 0)
            )

        else:

            tk.Label(
                container,
                text="DTR",
                bg=BG,
                fg=BLUE,
                font=(
                    "Segoe UI",
                    36,
                    "bold"
                )
            ).pack(
                pady=(65, 0)
            )

        # ----------------------------------------------------
        # NOMBRE
        # ----------------------------------------------------

        tk.Label(
            container,
            text="DTR",
            bg=BG,
            fg=TEXT,
            font=(
                "Segoe UI",
                16,
                "bold"
            )
        ).pack(
            pady=(5, 0)
        )

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        tk.Label(
            container,
            text="Iniciando...",
            bg=BG,
            fg=MUTED,
            font=(
                "Segoe UI",
                8
            )
        ).pack(
            pady=(2, 18)
        )

        self.splash = splash

        splash.after(
            1800,
            self.close_splash
        )

    # ========================================================
    # CERRAR SPLASH
    # ========================================================

    def close_splash(self):

        if hasattr(
            self,
            "splash"
        ):

            try:

                self.splash.destroy()

            except Exception:
                pass

            del self.splash

        self.root.deiconify()

        self.root.lift()

        self.root.focus_force()

    # ========================================================
    # ESTILOS
    # ========================================================

    def create_styles(self):

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except Exception:
            pass

        style.configure(
            "DTR.Horizontal.TProgressbar",
            troughcolor="#1a232e",
            background=BLUE,
            lightcolor=BLUE,
            darkcolor=BLUE,
            bordercolor="#1a232e",
            thickness=8
        )

        style.configure(
            "DTR.Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            bordercolor=BORDER,
            rowheight=25,
            font=(
                "Segoe UI",
                8
            )
        )

        style.configure(
            "DTR.Treeview.Heading",
            background=PANEL2,
            foreground=MUTED,
            bordercolor=BORDER,
            font=(
                "Segoe UI",
                7,
                "bold"
            )
        )

        style.map(
            "DTR.Treeview",
            background=[
                (
                    "selected",
                    "#185abd"
                )
            ],
            foreground=[
                (
                    "selected",
                    "#ffffff"
                )
            ]
        )

    # ========================================================
    # INTERFAZ
    # ========================================================

    def create_interface(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self.root,
            bg=BG
        )

        header.pack(
            fill="x",
            padx=18,
            pady=(12, 4)
        )

        # ----------------------------------------------------
        # INFORMACIÓN IZQUIERDA
        # ----------------------------------------------------

        left_header = tk.Frame(
            header,
            bg=BG
        )

        left_header.pack(
            side="left"
        )

        tk.Label(
            left_header,
            text="192.168.0.0/24",
            bg=BG,
            fg=MUTED,
            font=(
                "Consolas",
                8
            )
        ).pack(
            side="left",
            pady=(5, 0)
        )

        # ----------------------------------------------------
        # HEADER DERECHO
        # ----------------------------------------------------

        right_header = tk.Frame(
            header,
            bg=BG
        )

        right_header.pack(
            side="right"
        )

        # ----------------------------------------------------
        # LOGO SUPERIOR DERECHO
        # ----------------------------------------------------

        header_logo = load_logo(
            "DTR.png",
            (120, 120)
        )

        if header_logo:

            logo_label = tk.Label(
                right_header,
                image=header_logo,
                bg=BG
            )

            self.header_logo = header_logo

            logo_label.pack(
                side="right",
                padx=(10, 0)
            )

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        self.status_label = tk.Label(
            right_header,
            text="● ONLINE",
            bg=BG,
            fg=GREEN,
            font=(
                "Segoe UI",
                8,
                "bold"
            )
        )

        self.status_label.pack(
            side="right",
            padx=10
        )

        # ----------------------------------------------------
        # RELOJ
        # ----------------------------------------------------

        self.clock_label = tk.Label(
            right_header,
            text="00:00:00",
            bg=BG,
            fg=MUTED,
            font=(
                "Consolas",
                8
            )
        )

        self.clock_label.pack(
            side="right"
        )

        # ----------------------------------------------------
        # MÉTRICAS
        # ----------------------------------------------------

        metrics = tk.Frame(
            self.root,
            bg=BG
        )

        metrics.pack(
            fill="x",
            padx=18,
            pady=7
        )

        self.metric_devices = self.metric(
            metrics,
            "DEVICES",
            "0",
            CYAN
        )

        self.metric_done = self.metric(
            metrics,
            "DONE",
            "0",
            GREEN
        )

        self.metric_pending = self.metric(
            metrics,
            "PENDING",
            "0",
            YELLOW
        )

        self.metric_deleted = self.metric(
            metrics,
            "DELETED",
            "0",
            BLUE
        )

        self.metric_skipped = self.metric(
            metrics,
            "SKIPPED",
            "0",
            RED
        )

        self.metric_runtime = self.metric(
            metrics,
            "TIME",
            "00:00",
            PURPLE
        )

        # ----------------------------------------------------
        # CONTENEDOR PRINCIPAL
        # ----------------------------------------------------

        main = tk.Frame(
            self.root,
            bg=BG
        )

        main.pack(
            fill="both",
            expand=True,
            padx=18
        )

        # ====================================================
        # EQUIPOS
        # ====================================================

        devices = self.panel(
            main,
            "DEVICES"
        )

        devices.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        toolbar = tk.Frame(
            devices,
            bg=PANEL
        )

        toolbar.pack(
            fill="x",
            padx=8,
            pady=7
        )

        self.search_var = tk.StringVar()

        self.search_var.trace_add(
            "write",
            self.filter_devices
        )

        search = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            bg=BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=(
                "Consolas",
                8
            )
        )

        search.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=6
        )

        self.device_count_label = tk.Label(
            toolbar,
            text="0",
            bg=PANEL,
            fg=CYAN,
            font=(
                "Consolas",
                9,
                "bold"
            )
        )

        self.device_count_label.pack(
            side="right",
            padx=(8, 2)
        )

        # ----------------------------------------------------
        # TREE DE EQUIPOS
        # ----------------------------------------------------

        tree_frame = tk.Frame(
            devices,
            bg=PANEL
        )

        tree_frame.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=(0, 7)
        )

        self.device_tree = ttk.Treeview(
            tree_frame,
            columns=(
                "ip",
                "status"
            ),
            show="headings",
            selectmode="extended",
            style="DTR.Treeview"
        )

        self.device_tree.heading(
            "ip",
            text="IP ADDRESS"
        )

        self.device_tree.heading(
            "status",
            text="STATUS"
        )

        self.device_tree.column(
            "ip",
            width=150,
            anchor="w"
        )

        self.device_tree.column(
            "status",
            width=140,
            anchor="w"
        )

        device_scroll = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.device_tree.yview
        )

        self.device_tree.configure(
            yscrollcommand=device_scroll.set
        )

        self.device_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        device_scroll.pack(
            side="right",
            fill="y"
        )

        self.device_tree.bind(
            "<<TreeviewSelect>>",
            self.selection_changed
        )

        # ====================================================
        # OPERACIÓN
        # ====================================================

        operation = self.panel(
            main,
            "CURRENT OPERATION"
        )

        operation.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(5, 0)
        )

        self.operation_status = tk.Label(
            operation,
            text="READY",
            bg=PANEL,
            fg=TEXT,
            font=(
                "Segoe UI",
                13,
                "bold"
            )
        )

        self.operation_status.pack(
            pady=(12, 2)
        )

        self.operation_ip = tk.Label(
            operation,
            text="No active device",
            bg=PANEL,
            fg=CYAN,
            font=(
                "Consolas",
                10,
                "bold"
            )
        )

        self.operation_ip.pack(
            pady=(0, 8)
        )

        self.activity_label = tk.Label(
            operation,
            text="●",
            bg=PANEL,
            fg=BLUE,
            font=(
                "Segoe UI",
                28
            )
        )

        self.activity_label.pack(
            pady=2
        )

        self.separator(
            operation
        )

        # ----------------------------------------------------
        # PATH
        # ----------------------------------------------------

        tk.Label(
            operation,
            text="PATH",
            bg=PANEL,
            fg=MUTED,
            font=(
                "Segoe UI",
                7,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=12,
            pady=(8, 2)
        )

        self.path_label = tk.Label(
            operation,
            text="—",
            bg=PANEL2,
            fg=TEXT,
            anchor="w",
            justify="left",
            wraplength=400,
            padx=7,
            pady=6,
            font=(
                "Consolas",
                7
            )
        )

        self.path_label.pack(
            fill="x",
            padx=12
        )

        # ----------------------------------------------------
        # FILE / DIRECTORY
        # ----------------------------------------------------

        tk.Label(
            operation,
            text="FILE / DIRECTORY",
            bg=PANEL,
            fg=MUTED,
            font=(
                "Segoe UI",
                7,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=12,
            pady=(7, 2)
        )

        self.file_label = tk.Label(
            operation,
            text="—",
            bg=PANEL2,
            fg=CYAN,
            anchor="w",
            justify="left",
            wraplength=400,
            padx=7,
            pady=6,
            font=(
                "Consolas",
                7
            )
        )

        self.file_label.pack(
            fill="x",
            padx=12
        )

        # ----------------------------------------------------
        # FILE PROGRESS
        # ----------------------------------------------------

        tk.Label(
            operation,
            text="FILE PROGRESS",
            bg=PANEL,
            fg=MUTED,
            font=(
                "Segoe UI",
                7,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=12,
            pady=(7, 2)
        )

        self.file_progress = ttk.Progressbar(
            operation,
            style="DTR.Horizontal.TProgressbar",
            mode="determinate"
        )

        self.file_progress.pack(
            fill="x",
            padx=12
        )

        self.file_progress_text = tk.Label(
            operation,
            text="0 / 0",
            bg=PANEL,
            fg=MUTED,
            font=(
                "Consolas",
                7
            )
        )

        self.file_progress_text.pack(
            anchor="e",
            padx=12,
            pady=(2, 4)
        )

        # ====================================================
        # PENDIENTES
        # ====================================================

        pending = self.panel(
            self.root,
            "PENDING / ERRORS"
        )

        pending.pack(
            fill="x",
            padx=18,
            pady=(8, 0)
        )

        pending_frame = tk.Frame(
            pending,
            bg=PANEL
        )

        pending_frame.pack(
            fill="x",
            padx=7,
            pady=6
        )

        self.pending_tree = ttk.Treeview(
            pending_frame,
            columns=(
                "ip",
                "error",
                "description",
                "attempts"
            ),
            show="headings",
            selectmode="extended",
            height=3,
            style="DTR.Treeview"
        )

        pending_columns = {
            "ip": ("IP", 130),
            "error": ("ERROR", 145),
            "description": ("DESCRIPTION", 430),
            "attempts": ("TRIES", 60)
        }

        for column, data in pending_columns.items():

            self.pending_tree.heading(
                column,
                text=data[0]
            )

            self.pending_tree.column(
                column,
                width=data[1]
            )

        pending_scroll = ttk.Scrollbar(
            pending_frame,
            orient="vertical",
            command=self.pending_tree.yview
        )

        self.pending_tree.configure(
            yscrollcommand=pending_scroll.set
        )

        self.pending_tree.pack(
            side="left",
            fill="x",
            expand=True
        )

        pending_scroll.pack(
            side="right",
            fill="y"
        )

        # ====================================================
        # CONTROLES
        # ====================================================

        controls = tk.Frame(
            self.root,
            bg=BG
        )

        controls.pack(
            fill="x",
            padx=18,
            pady=7
        )

        self.scan_button = self.button(
            controls,
            "SCAN",
            BLUE,
            self.start_scan
        )

        self.scan_button.pack(
            side="left",
            padx=(0, 4)
        )

        self.clean_selected_button = self.button(
            controls,
            "CLEAN SELECTED",
            GREEN,
            self.clean_selected
        )

        self.clean_selected_button.pack(
            side="left",
            padx=2
        )

        self.clean_pending_button = self.button(
            controls,
            "CLEAN PENDING",
            PURPLE,
            self.clean_all_pending
        )

        self.clean_pending_button.pack(
            side="left",
            padx=2
        )

        self.retry_button = self.button(
            controls,
            "↻ RETRY",
            YELLOW,
            self.retry_selected
        )

        self.retry_button.pack(
            side="left",
            padx=2
        )

        self.stop_button = self.button(
            controls,
            "STOP",
            RED,
            self.stop_process
        )

        self.stop_button.pack(
            side="right"
        )

        self.stop_button.config(
            state="disabled"
        )

        # ====================================================
        # LIVE CONSOLE
        # ====================================================

        console = self.panel(
            self.root,
            "LIVE"
        )

        console.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        self.console = tk.Text(
            console,
            height=3,
            bg="#05080c",
            fg="#91a0af",
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            font=(
                "Consolas",
                7
            )
        )

        self.console.pack(
            fill="x",
            padx=7,
            pady=5
        )

    # ========================================================
    # WIDGET PANEL
    # ========================================================

    def panel(
        self,
        parent,
        title
    ):

        frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        titlebar = tk.Frame(
            frame,
            bg=PANEL
        )

        titlebar.pack(
            fill="x"
        )

        tk.Label(
            titlebar,
            text=title,
            bg=PANEL,
            fg=MUTED,
            font=(
                "Segoe UI",
                7,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=10,
            pady=6
        )

        tk.Frame(
            frame,
            bg=BORDER,
            height=1
        ).pack(
            fill="x"
        )

        return frame

    # ========================================================
    # MÉTRICA
    # ========================================================

    def metric(
        self,
        parent,
        title,
        value,
        color
    ):

        frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=2
        )

        tk.Label(
            frame,
            text=title,
            bg=PANEL,
            fg=MUTED,
            font=(
                "Segoe UI",
                6,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=8,
            pady=(5, 0)
        )

        label = tk.Label(
            frame,
            text=value,
            bg=PANEL,
            fg=color,
            font=(
                "Segoe UI",
                14,
                "bold"
            )
        )

        label.pack(
            anchor="w",
            padx=8,
            pady=(0, 4)
        )

        return label

    # ========================================================
    # BOTÓN
    # ========================================================

    def button(
        self,
        parent,
        text,
        color,
        command
    ):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=6,
            font=(
                "Segoe UI",
                7,
                "bold"
            ),
            cursor="hand2"
        )

    # ========================================================
    # SEPARADOR
    # ========================================================

    def separator(
        self,
        parent
    ):

        tk.Frame(
            parent,
            bg=BORDER,
            height=1
        ).pack(
            fill="x",
            padx=12,
            pady=4
        )

    # ========================================================
    # RELOJ
    # ========================================================

    def update_clock(self):

        self.clock_label.config(
            text=datetime.now().strftime(
                "%H:%M:%S"
            )
        )

        if (
            self.cleaning
            and self.start_time
        ):

            elapsed = int(
                time.time()
                - self.start_time
            )

            minutes = elapsed // 60
            seconds = elapsed % 60

            self.metric_runtime.config(
                text=f"{minutes:02d}:{seconds:02d}"
            )

        self.root.after(
            1000,
            self.update_clock
        )

    # ========================================================
    # LOG
    # ========================================================

    def log(
        self,
        message
    ):

        def write():

            timestamp = datetime.now().strftime(
                "%H:%M:%S"
            )

            self.console.insert(
                "end",
                f"[{timestamp}] {message}\n"
            )

            self.console.see(
                "end"
            )

        self.root.after(
            0,
            write
        )

    # ========================================================
    # ESCANEO
    # ========================================================

    def start_scan(self):

        if (
            self.scanning
            or self.cleaning
        ):
            return

        self.clear_devices()

        self.active_ips = []

        self.scanning = True

        self.stop_requested = False

        self.set_controls(
            False
        )

        self.stop_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● SCANNING",
            fg=YELLOW
        )

        self.operation_status.config(
            text="SCANNING"
        )

        self.operation_ip.config(
            text="192.168.0.0/24"
        )

        self.activity_label.config(
            text="◌",
            fg=YELLOW
        )

        self.log(
            "Escaneando 192.168.0.1 - 192.168.0.254..."
        )

        threading.Thread(
            target=self.scan_worker,
            daemon=True
        ).start()

    # ========================================================
    # WORKER DE ESCANEO
    # ========================================================

    def scan_worker(self):

        found = []

        for number in range(
            IP_START,
            IP_END + 1
        ):

            if self.stop_requested:
                break

            ip = (
                f"{NETWORK_PREFIX}{number}"
            )

            try:

                result = subprocess.run(
                    [
                        "ping",
                        "-n",
                        "1",
                        "-w",
                        "350",
                        ip
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode == 0:

                    found.append(
                        ip
                    )

                    self.root.after(
                        0,
                        lambda address=ip:
                        self.add_device(address)
                    )

                    self.log(
                        f"● ONLINE  {ip}"
                    )

            except Exception as error:

                self.log(
                    f"! {ip}: {error}"
                )

        self.active_ips = found

        self.root.after(
            0,
            self.scan_finished
        )

    # ========================================================
    # ESCANEO FINALIZADO
    # ========================================================

    def scan_finished(self):

        self.scanning = False

        self.set_controls(
            True
        )

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="● ONLINE",
            fg=GREEN
        )

        self.operation_status.config(
            text="SCAN COMPLETE"
        )

        self.activity_label.config(
            text="✓",
            fg=GREEN
        )

        self.metric_devices.config(
            text=str(
                len(
                    self.active_ips
                )
            )
        )

        self.device_count_label.config(
            text=str(
                len(
                    self.active_ips
                )
            )
        )

        self.log(
            f"Escaneo terminado: "
            f"{len(self.active_ips)} equipos encontrados."
        )

    # ========================================================
    # EQUIPOS
    # ========================================================

    def add_device(
        self,
        ip
    ):

        if ip in self.history["completed"]:

            status = "✓ COMPLETED"

        elif ip in self.history["pending"]:

            status = "⚠ PENDING"

        else:

            status = "● ONLINE"

        self.device_tree.insert(
            "",
            "end",
            values=(
                ip,
                status
            )
        )

    # ========================================================
    # LIMPIAR EQUIPOS
    # ========================================================

    def clear_devices(self):

        for item in self.device_tree.get_children():

            self.device_tree.delete(
                item
            )

    # ========================================================
    # FILTRAR EQUIPOS
    # ========================================================

    def filter_devices(
        self,
        *args
    ):

        query = (
            self.search_var
            .get()
            .lower()
        )

        for item in self.device_tree.get_children():

            values = self.device_tree.item(
                item,
                "values"
            )

            if not values:
                continue

            ip = values[0]

            if query not in ip.lower():

                self.device_tree.detach(
                    item
                )

            else:

                self.device_tree.reattach(
                    item,
                    "",
                    "end"
                )

    # ========================================================
    # SELECCIÓN
    # ========================================================

    def selection_changed(
        self,
        event=None
    ):

        selected = self.device_tree.selection()

        if not selected:
            return

        values = self.device_tree.item(
            selected[0],
            "values"
        )

        if not values:
            return

        ip = values[0]

        self.operation_ip.config(
            text=ip
        )

        if ip in self.history["completed"]:

            self.operation_status.config(
                text="COMPLETED"
            )

            self.activity_label.config(
                text="✓",
                fg=GREEN
            )

        elif ip in self.history["pending"]:

            self.operation_status.config(
                text="PENDING"
            )

            self.activity_label.config(
                text="⚠",
                fg=YELLOW
            )

        else:

            self.operation_status.config(
                text="ONLINE"
            )

            self.activity_label.config(
                text="●",
                fg=CYAN
            )

    # ========================================================
    # IP SELECCIONADAS
    # ========================================================

    def selected_ips(self):

        ips = []

        for item in self.device_tree.selection():

            values = self.device_tree.item(
                item,
                "values"
            )

            if values:

                ips.append(
                    values[0]
                )

        return ips

    # ========================================================
    # LIMPIAR SELECCIONADOS
    # ========================================================

    def clean_selected(self):

        ips = self.selected_ips()

        if not ips:

            messagebox.showwarning(
                "DTR",
                "Selecciona uno o más equipos."
            )

            return

        ips = [
            ip
            for ip in ips
            if ip not in self.history["completed"]
        ]

        if not ips:

            messagebox.showinfo(
                "DTR",
                "Los equipos seleccionados "
                "ya están completados."
            )

            return

        self.start_cleaning(
            ips
        )

    # ========================================================
    # LIMPIAR PENDIENTES
    # ========================================================

    def clean_all_pending(self):

        if not self.active_ips:

            messagebox.showwarning(
                "DTR",
                "Primero realiza un escaneo."
            )

            return

        ips = [
            ip
            for ip in self.active_ips
            if ip not in self.history["completed"]
        ]

        if not ips:

            messagebox.showinfo(
                "DTR",
                "No existen equipos pendientes."
            )

            return

        self.start_cleaning(
            ips
        )

    # ========================================================
    # REINTENTAR
    # ========================================================

    def retry_selected(self):

        selected = self.pending_tree.selection()

        if not selected:

            messagebox.showwarning(
                "DTR",
                "Selecciona uno o más equipos "
                "del historial."
            )

            return

        ips = []

        for item in selected:

            values = self.pending_tree.item(
                item,
                "values"
            )

            if values:

                ips.append(
                    values[0]
                )

        self.start_cleaning(
            ips
        )

    # ========================================================
    # INICIAR LIMPIEZA
    # ========================================================

    def start_cleaning(
        self,
        ips
    ):

        if self.cleaning:
            return

        ips = [
            ip
            for ip in ips
            if ip not in self.history["completed"]
        ]

        if not ips:
            return

        self.cleaning = True

        self.stop_requested = False

        self.total_devices = len(
            ips
        )

        self.processed_devices = 0

        self.deleted_files = 0

        self.skipped_files = 0

        self.start_time = time.time()

        self.metric_runtime.config(
            text="00:00"
        )

        self.metric_deleted.config(
            text="0"
        )

        self.metric_skipped.config(
            text="0"
        )

        self.set_controls(
            False
        )

        self.stop_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● CLEANING",
            fg=CYAN
        )

        self.operation_status.config(
            text="CLEANING"
        )

        self.activity_label.config(
            text="◉",
            fg=CYAN
        )

        self.log(
            f"Iniciando limpieza de "
            f"{len(ips)} equipo(s)."
        )

        threading.Thread(
            target=self.clean_worker,
            args=(ips,),
            daemon=True
        ).start()

    # ========================================================
    # WORKER PRINCIPAL
    # ========================================================

    def clean_worker(
        self,
        ips
    ):

        for ip in ips:

            if self.stop_requested:
                break

            self.set_device_status(
                ip,
                "◉ CLEANING"
            )

            self.log(
                f"→ Procesando {ip}"
            )

            success, error_type, description = (
                self.clean_remote(
                    ip
                )
            )

            if success:

                self.mark_completed(
                    ip
                )

                self.set_device_status(
                    ip,
                    "✓ COMPLETED"
                )

                self.log(
                    f"✓ {ip} completado."
                )

            else:

                self.mark_pending(
                    ip,
                    error_type,
                    description
                )

                self.set_device_status(
                    ip,
                    "⚠ PENDING"
                )

                self.log(
                    f"! {ip} pendiente: "
                    f"{error_type}"
                )

            self.processed_devices += 1

            self.root.after(
                0,
                self.update_metrics
            )

        self.root.after(
            0,
            self.clean_finished
        )

    # ========================================================
    # LIMPIEZA REMOTA
    # ========================================================

    def clean_remote(
        self,
        ip
    ):

        share = (
            rf"\\{ip}\C$"
        )

        self.update_operation(
            ip,
            share,
            "Comprobando acceso..."
        )

        # ----------------------------------------------------
        # COMPROBAR ACCESO
        # ----------------------------------------------------

        try:

            if not os.path.exists(
                share
            ):

                return (
                    False,
                    "CONNECTION / ACCESS",
                    "No fue posible acceder a C$. "
                    "Comprueba conectividad, SMB, "
                    "Firewall y permisos."
                )

        except PermissionError:

            return (
                False,
                "CREDENTIALS",
                "Acceso denegado al recurso "
                "administrativo C$."
            )

        except OSError as error:

            return (
                False,
                "CONNECTION",
                str(error)
            )

        # ----------------------------------------------------
        # CARPETAS A LIMPIAR
        # ----------------------------------------------------

        folders = []

        system_temp = (
            rf"\\{ip}\C$\Windows\Temp"
        )

        if os.path.isdir(
            system_temp
        ):

            folders.append(
                system_temp
            )

        users_path = (
            rf"\\{ip}\C$\Users"
        )

        try:

            users = os.listdir(
                users_path
            )

            for user in users:

                temp_path = os.path.join(
                    users_path,
                    user,
                    "AppData",
                    "Local",
                    "Temp"
                )

                if os.path.isdir(
                    temp_path
                ):

                    folders.append(
                        temp_path
                    )

        except PermissionError:

            return (
                False,
                "PERMISSION",
                "No fue posible acceder a C:\\Users."
            )

        except OSError as error:

            return (
                False,
                "ACCESS",
                str(error)
            )

        # ----------------------------------------------------
        # LIMPIAR
        # ----------------------------------------------------

        for folder in folders:

            if self.stop_requested:

                return (
                    False,
                    "STOPPED",
                    "Operación detenida por el usuario."
                )

            self.clean_folder(
                ip,
                folder
            )

        return (
            True,
            "",
            ""
        )

    # ========================================================
    # LIMPIAR CARPETA
    # ========================================================

    def clean_folder(
        self,
        ip,
        folder
    ):

        try:

            items = list(
                Path(folder).iterdir()
            )

        except PermissionError:

            self.skipped_files += 1

            self.log(
                f"🔒 Sin permisos: {folder}"
            )

            return

        except OSError:

            self.skipped_files += 1

            self.log(
                f"! No accesible: {folder}"
            )

            return

        total = len(
            items
        )

        self.root.after(
            0,
            lambda total_items=total:
            self.configure_file_progress(
                total_items
            )
        )

        for index, item in enumerate(
            items,
            start=1
        ):

            if self.stop_requested:
                return

            self.update_operation(
                ip,
                folder,
                item.name
            )

            try:

                # ------------------------------------------------
                # ARCHIVO
                # ------------------------------------------------

                if (
                    item.is_file()
                    or item.is_symlink()
                ):

                    item.unlink()

                    self.deleted_files += 1

                    self.log(
                        f"🗑 {item.name}"
                    )

                # ------------------------------------------------
                # DIRECTORIO
                # ------------------------------------------------

                elif item.is_dir():

                    shutil.rmtree(
                        item
                    )

                    self.deleted_files += 1

                    self.log(
                        f"🗑 {item.name}\\"
                    )

            except PermissionError:

                self.skipped_files += 1

                self.log(
                    f"🔒 BLOQUEADO: {item.name}"
                )

            except FileNotFoundError:

                self.log(
                    f"↪ Ya no existe: {item.name}"
                )

            except OSError as error:

                self.skipped_files += 1

                self.log(
                    f"! OMITIDO: {item.name}"
                )

            self.root.after(
                0,
                lambda current=index,
                total_items=total:
                self.update_file_progress(
                    current,
                    total_items
                )
            )

            self.root.after(
                0,
                self.update_metrics
            )

                # ========================================================
    # ESCANEO
    # ========================================================

    def start_scan(self):
        if self.scanning or self.cleaning:
            return

        self.clear_devices()
        self.active_ips = []
        self.scanning = True
        self.stop_requested = False

        self.set_controls(False)

        self.stop_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● SCANNING",
            fg=YELLOW
        )

        self.operation_status.config(
            text="SCANNING"
        )

        self.operation_ip.config(
            text="192.168.0.0/24"
        )

        self.activity_label.config(
            text="◌",
            fg=YELLOW
        )

        self.log(
            "Escaneando 192.168.0.1 - 192.168.0.254..."
        )

        threading.Thread(
            target=self.scan_worker,
            daemon=True
        ).start()

    def scan_worker(self):

        found = []

        for number in range(
            IP_START,
            IP_END + 1
        ):

            if self.stop_requested:
                break

            ip = f"{NETWORK_PREFIX}{number}"

            try:

                result = subprocess.run(
                    [
                        "ping",
                        "-n",
                        "1",
                        "-w",
                        "350",
                        ip
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode == 0:

                    found.append(ip)

                    self.root.after(
                        0,
                        lambda address=ip:
                        self.add_device(address)
                    )

                    self.log(
                        f"● ONLINE  {ip}"
                    )

            except Exception as error:

                self.log(
                    f"! {ip}: {error}"
                )

        self.active_ips = found

        self.root.after(
            0,
            self.scan_finished
        )

    def scan_finished(self):

        self.scanning = False

        self.set_controls(True)

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="● ONLINE",
            fg=GREEN
        )

        self.operation_status.config(
            text="SCAN COMPLETE"
        )

        self.activity_label.config(
            text="✓",
            fg=GREEN
        )

        self.metric_devices.config(
            text=str(
                len(self.active_ips)
            )
        )

        self.device_count_label.config(
            text=str(
                len(self.active_ips)
            )
        )

        self.log(
            f"Escaneo terminado: "
            f"{len(self.active_ips)} equipos encontrados."
        )

    # ========================================================
    # EQUIPOS
    # ========================================================

    def add_device(self, ip):

        status = self.get_device_status(ip)

        self.device_tree.insert(
            "",
            "end",
            values=(
                ip,
                status
            )
        )

    def clear_devices(self):

        for item in self.device_tree.get_children():

            self.device_tree.delete(
                item
            )

    def filter_devices(self, *args):

        query = (
            self.search_var
            .get()
            .lower()
        )

        for item in self.device_tree.get_children():

            values = self.device_tree.item(
                item,
                "values"
            )

            if not values:
                continue

            ip = values[0]

            if query not in ip.lower():

                self.device_tree.detach(
                    item
                )

            else:

                self.device_tree.reattach(
                    item,
                    "",
                    "end"
                )

    # ========================================================
    # ESTADO DEL EQUIPO
    # ========================================================

    def get_device_status(self, ip):

        if ip in self.history["completed"]:

            if self.can_run_completed(ip):

                return "↻ READY AGAIN"

            return "✓ COMPLETED"

        if ip in self.history["pending"]:

            return "⚠ PENDING"

        return "● ONLINE"

    # ========================================================
    # COMPROBAR SI UN EQUIPO COMPLETADO
    # PUEDE VOLVERSE A PROCESAR
    # ========================================================

    def can_run_completed(self, ip):

        data = self.history["completed"].get(ip)

        if not data:
            return True

        completed_at = data.get(
            "completed_at"
        )

        if not completed_at:
            return True

        try:

            completed_time = datetime.fromisoformat(
                completed_at
            )

            elapsed = (
                datetime.now()
                - completed_time
            )

            hours = (
                elapsed.total_seconds()
                / 3600
            )

            return (
                hours
                >= COMPLETED_COOLDOWN_HOURS
            )

        except Exception:

            return True

    # ========================================================
    # TIEMPO RESTANTE PARA VOLVER A PROCESAR
    # ========================================================

    def remaining_cooldown(self, ip):

        data = self.history["completed"].get(ip)

        if not data:
            return 0

        completed_at = data.get(
            "completed_at"
        )

        if not completed_at:
            return 0

        try:

            completed_time = datetime.fromisoformat(
                completed_at
            )

            cooldown_seconds = (
                COMPLETED_COOLDOWN_HOURS
                * 3600
            )

            elapsed = (
                datetime.now()
                - completed_time
            ).total_seconds()

            remaining = (
                cooldown_seconds
                - elapsed
            )

            return max(
                0,
                int(remaining)
            )

        except Exception:

            return 0

    # ========================================================
    # TEXTO DEL TIEMPO RESTANTE
    # ========================================================

    def cooldown_text(self, ip):

        seconds = self.remaining_cooldown(
            ip
        )

        if seconds <= 0:
            return "READY AGAIN"

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        secs = (
            seconds % 60
        )

        if hours > 0:

            return (
                f"WAIT {hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}"
            )

        return (
            f"WAIT {minutes:02d}:"
            f"{secs:02d}"
        )

    # ========================================================
    # SELECCIÓN
    # ========================================================

    def selection_changed(self, event=None):

        selected = self.device_tree.selection()

        if not selected:
            return

        values = self.device_tree.item(
            selected[0],
            "values"
        )

        if not values:
            return

        ip = values[0]

        self.operation_ip.config(
            text=ip
        )

        # ----------------------------------------------------
        # COMPLETADO
        # ----------------------------------------------------

        if ip in self.history["completed"]:

            if self.can_run_completed(ip):

                self.operation_status.config(
                    text="READY AGAIN"
                )

                self.activity_label.config(
                    text="↻",
                    fg=BLUE
                )

                self.log(
                    f"{ip} puede volver a procesarse."
                )

            else:

                remaining = self.cooldown_text(
                    ip
                )

                self.operation_status.config(
                    text="COMPLETED"
                )

                self.activity_label.config(
                    text="✓",
                    fg=GREEN
                )

                self.log(
                    f"{ip}: {remaining}"
                )

        # ----------------------------------------------------
        # PENDIENTE
        # ----------------------------------------------------

        elif ip in self.history["pending"]:

            self.operation_status.config(
                text="PENDING"
            )

            self.activity_label.config(
                text="⚠",
                fg=YELLOW
            )

        # ----------------------------------------------------
        # ONLINE
        # ----------------------------------------------------

        else:

            self.operation_status.config(
                text="ONLINE"
            )

            self.activity_label.config(
                text="●",
                fg=CYAN
            )

    # ========================================================
    # IP SELECCIONADAS
    # ========================================================

    def selected_ips(self):

        ips = []

        for item in self.device_tree.selection():

            values = self.device_tree.item(
                item,
                "values"
            )

            if values:

                ips.append(
                    values[0]
                )

        return ips

    # ========================================================
    # LIMPIAR SELECCIONADOS
    # ========================================================

    def clean_selected(self):

        ips = self.selected_ips()

        if not ips:

            messagebox.showwarning(
                "DTR",
                "Selecciona uno o más equipos."
            )

            return

        valid_ips = []

        blocked_ips = []

        for ip in ips:

            # ------------------------------------------------
            # SI NUNCA SE HA COMPLETADO
            # ------------------------------------------------

            if ip not in self.history["completed"]:

                valid_ips.append(ip)
                continue

            # ------------------------------------------------
            # SI YA SE COMPLETÓ PERO YA PASÓ EL COOLDOWN
            # ------------------------------------------------

            if self.can_run_completed(ip):

                valid_ips.append(ip)

            else:

                blocked_ips.append(ip)

        # ----------------------------------------------------
        # AVISO DE EQUIPOS BLOQUEADOS
        # ----------------------------------------------------

        if blocked_ips:

            for ip in blocked_ips:

                remaining = self.cooldown_text(
                    ip
                )

                self.log(
                    f"⏳ {ip} no disponible: "
                    f"{remaining}"
                )

        # ----------------------------------------------------
        # NINGUNO DISPONIBLE
        # ----------------------------------------------------

        if not valid_ips:

            messagebox.showinfo(
                "DTR",
                "Los equipos seleccionados "
                "ya fueron procesados y todavía "
                "no cumplen el tiempo para volver "
                "a ejecutar la limpieza."
            )

            return

        self.start_cleaning(
            valid_ips
        )

    # ========================================================
    # LIMPIAR TODOS LOS PENDIENTES / DISPONIBLES
    # ========================================================

    def clean_all_pending(self):

        if not self.active_ips:

            messagebox.showwarning(
                "DTR",
                "Primero realiza un escaneo."
            )

            return

        ips = []

        blocked = []

        for ip in self.active_ips:

            # ------------------------------------------------
            # NUEVO EQUIPO
            # ------------------------------------------------

            if ip not in self.history["completed"]:

                ips.append(ip)
                continue

            # ------------------------------------------------
            # EQUIPO COMPLETADO Y DISPONIBLE
            # ------------------------------------------------

            if self.can_run_completed(ip):

                ips.append(ip)

            else:

                blocked.append(ip)

        if blocked:

            self.log(
                f"⏳ {len(blocked)} equipo(s) "
                f"todavía están dentro del periodo "
                f"de espera."
            )

        if not ips:

            messagebox.showinfo(
                "DTR",
                "No existen equipos disponibles "
                "para procesar."
            )

            return

        self.start_cleaning(
            ips
        )

    # ========================================================
    # REINTENTAR PENDIENTES
    # ========================================================

    def retry_selected(self):

        selected = self.pending_tree.selection()

        if not selected:

            messagebox.showwarning(
                "DTR",
                "Selecciona uno o más equipos "
                "del historial."
            )

            return

        ips = []

        for item in selected:

            values = self.pending_tree.item(
                item,
                "values"
            )

            if values:

                ips.append(
                    values[0]
                )

        self.start_cleaning(
            ips
        )

    # ========================================================
    # INICIAR LIMPIEZA
    # ========================================================

    def start_cleaning(self, ips):

        if self.cleaning:
            return

        valid_ips = []

        for ip in ips:

            # ------------------------------------------------
            # SI ESTÁ COMPLETADO
            # ------------------------------------------------

            if ip in self.history["completed"]:

                if self.can_run_completed(ip):

                    valid_ips.append(ip)

                else:

                    self.log(
                        f"⏳ {ip} todavía no puede "
                        f"volver a procesarse."
                    )

            else:

                valid_ips.append(ip)

        ips = valid_ips

        if not ips:
            return

        self.cleaning = True
        self.stop_requested = False

        self.total_devices = len(
            ips
        )

        self.processed_devices = 0
        self.deleted_files = 0
        self.skipped_files = 0

        self.start_time = time.time()

        self.metric_runtime.config(
            text="00:00"
        )

        self.metric_deleted.config(
            text="0"
        )

        self.metric_skipped.config(
            text="0"
        )

        self.set_controls(
            False
        )

        self.stop_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● CLEANING",
            fg=CYAN
        )

        self.operation_status.config(
            text="CLEANING"
        )

        self.activity_label.config(
            text="◉",
            fg=CYAN
        )

        self.log(
            f"Iniciando limpieza de "
            f"{len(ips)} equipo(s)."
        )

        threading.Thread(
            target=self.clean_worker,
            args=(ips,),
            daemon=True
        ).start()

    # ========================================================
    # WORKER PRINCIPAL
    # ========================================================

    def clean_worker(self, ips):

        for ip in ips:

            if self.stop_requested:
                break

            self.set_device_status(
                ip,
                "◉ CLEANING"
            )

            self.log(
                f"→ Procesando {ip}"
            )

            success, error_type, description = (
                self.clean_remote(ip)
            )

            if success:

                self.mark_completed(
                    ip
                )

                self.set_device_status(
                    ip,
                    "✓ COMPLETED"
                )

                self.log(
                    f"✓ {ip} completado."
                )

            else:

                self.mark_pending(
                    ip,
                    error_type,
                    description
                )

                self.set_device_status(
                    ip,
                    "⚠ PENDING"
                )

                self.log(
                    f"! {ip} pendiente: "
                    f"{error_type}"
                )

            self.processed_devices += 1

            self.root.after(
                0,
                self.update_metrics
            )

        self.root.after(
            0,
            self.clean_finished
        )

    # ========================================================
    # LIMPIEZA REMOTA
    # ========================================================

    def clean_remote(self, ip):

        share = rf"\\{ip}\C$"

        self.update_operation(
            ip,
            share,
            "Comprobando acceso..."
        )

        # ----------------------------------------------------
        # COMPROBAR ACCESO
        # ----------------------------------------------------

        try:

            if not os.path.exists(share):

                return (
                    False,
                    "CONNECTION / ACCESS",
                    "No fue posible acceder a C$. "
                    "Comprueba conectividad, SMB, "
                    "Firewall y permisos."
                )

        except PermissionError:

            return (
                False,
                "CREDENTIALS",
                "Acceso denegado al recurso "
                "administrativo C$."
            )

        except OSError as error:

            return (
                False,
                "CONNECTION",
                str(error)
            )

        # ----------------------------------------------------
        # CARPETAS A LIMPIAR
        # ----------------------------------------------------

        folders = []

        system_temp = (
            rf"\\{ip}\C$\Windows\Temp"
        )

        if os.path.isdir(system_temp):

            folders.append(
                system_temp
            )

        users_path = (
            rf"\\{ip}\C$\Users"
        )

        try:

            users = os.listdir(
                users_path
            )

            for user in users:

                temp_path = os.path.join(
                    users_path,
                    user,
                    "AppData",
                    "Local",
                    "Temp"
                )

                if os.path.isdir(temp_path):

                    folders.append(
                        temp_path
                    )

        except PermissionError:

            return (
                False,
                "PERMISSION",
                "No fue posible acceder "
                "a C:\\Users."
            )

        except OSError as error:

            return (
                False,
                "ACCESS",
                str(error)
            )

        # ----------------------------------------------------
        # LIMPIAR
        # ----------------------------------------------------

        for folder in folders:

            if self.stop_requested:

                return (
                    False,
                    "STOPPED",
                    "Operación detenida por el usuario."
                )

            self.clean_folder(
                ip,
                folder
            )

        return (
            True,
            "",
            ""
        )

    # ========================================================
    # LIMPIAR CARPETA
    # ========================================================

    def clean_folder(
        self,
        ip,
        folder
    ):

        try:

            items = list(
                Path(folder).iterdir()
            )

        except PermissionError:

            self.skipped_files += 1

            self.log(
                f"🔒 Sin permisos: {folder}"
            )

            return

        except OSError:

            self.skipped_files += 1

            self.log(
                f"! No accesible: {folder}"
            )

            return

        total = len(items)

        self.root.after(
            0,
            lambda total_items=total:
            self.configure_file_progress(
                total_items
            )
        )

        for index, item in enumerate(
            items,
            start=1
        ):

            if self.stop_requested:
                return

            self.update_operation(
                ip,
                folder,
                item.name
            )

            try:

                # --------------------------------------------
                # ARCHIVO
                # --------------------------------------------

                if (
                    item.is_file()
                    or item.is_symlink()
                ):

                    item.unlink()

                    self.deleted_files += 1

                    self.log(
                        f"🗑 {item.name}"
                    )

                # --------------------------------------------
                # DIRECTORIO
                # --------------------------------------------

                elif item.is_dir():

                    shutil.rmtree(
                        item
                    )

                    self.deleted_files += 1

                    self.log(
                        f"🗑 {item.name}\\"
                    )

            except PermissionError:

                self.skipped_files += 1

                self.log(
                    f"🔒 BLOQUEADO: {item.name}"
                )

            except FileNotFoundError:

                self.log(
                    f"↪ Ya no existe: {item.name}"
                )

            except OSError as error:

                self.skipped_files += 1

                self.log(
                    f"! OMITIDO: {item.name}"
                )

            self.root.after(
                0,
                lambda current=index,
                total_items=total:
                self.update_file_progress(
                    current,
                    total_items
                )
            )

            self.root.after(
                0,
                self.update_metrics
            )

    # ========================================================
    # HISTORIAL COMPLETADOS
    # ========================================================

    def mark_completed(self, ip):

        self.history["completed"][ip] = {
            "completed_at":
                datetime.now().isoformat(
                    timespec="seconds"
                )
        }

        self.history["pending"].pop(
            ip,
            None
        )

        save_history(
            self.history
        )

        self.root.after(
            0,
            self.refresh_pending
        )

    # ========================================================
    # HISTORIAL PENDIENTES
    # ========================================================

    def mark_pending(
        self,
        ip,
        error,
        description
    ):

        old = self.history[
            "pending"
        ].get(
            ip,
            {}
        )

        attempts = int(
            old.get(
                "attempts",
                0
            )
        ) + 1

        self.history[
            "pending"
        ][ip] = {

            "error": error,

            "description": description,

            "attempts": attempts,

            "last_attempt":
                datetime.now().isoformat(
                    timespec="seconds"
                )
        }

        save_history(
            self.history
        )

        self.root.after(
            0,
            self.refresh_pending
        )

    # ========================================================
    # REFRESCAR PENDIENTES
    # ========================================================

    def refresh_pending(self):

        for item in self.pending_tree.get_children():

            self.pending_tree.delete(
                item
            )

        for ip, data in sorted(
            self.history[
                "pending"
            ].items()
        ):

            self.pending_tree.insert(
                "",
                "end",
                values=(
                    ip,
                    data.get(
                        "error",
                        "UNKNOWN"
                    ),
                    data.get(
                        "description",
                        ""
                    ),
                    data.get(
                        "attempts",
                        0
                    )
                )
            )

        self.metric_pending.config(
            text=str(
                len(
                    self.history[
                        "pending"
                    ]
                )
            )
        )

        self.metric_done.config(
            text=str(
                len(
                    self.history[
                        "completed"
                    ]
                )
            )
        )

    # ========================================================
    # ACTUALIZAR OPERACIÓN
    # ========================================================

    def update_operation(
        self,
        ip,
        path,
        filename
    ):

        self.root.after(
            0,
            lambda:
            self._operation(
                ip,
                path,
                filename
            )
        )

    def _operation(
        self,
        ip,
        path,
        filename
    ):

        self.operation_ip.config(
            text=ip
        )

        self.path_label.config(
            text=path
        )

        self.file_label.config(
            text=filename
        )

    # ========================================================
    # PROGRESO
    # ========================================================

    def configure_file_progress(
        self,
        total
    ):

        self.file_progress["maximum"] = max(
            1,
            total
        )

        self.file_progress["value"] = 0

        self.file_progress_text.config(
            text=f"0 / {total}"
        )

    def update_file_progress(
        self,
        current,
        total
    ):

        self.file_progress["maximum"] = max(
            1,
            total
        )

        self.file_progress["value"] = current

        self.file_progress_text.config(
            text=f"{current} / {total}"
        )

    # ========================================================
    # ESTADO DE EQUIPO
    # ========================================================

    def set_device_status(
        self,
        ip,
        status
    ):

        def update():

            for item in self.device_tree.get_children():

                values = self.device_tree.item(
                    item,
                    "values"
                )

                if (
                    values
                    and values[0] == ip
                ):

                    self.device_tree.item(
                        item,
                        values=(
                            ip,
                            status
                        )
                    )

                    break

        self.root.after(
            0,
            update
        )

    # ========================================================
    # ACTUALIZAR ESTADOS DESPUÉS DEL COOLDOWN
    # ========================================================

    def refresh_completed_statuses(self):

        for item in self.device_tree.get_children():

            values = self.device_tree.item(
                item,
                "values"
            )

            if not values:
                continue

            ip = values[0]

            if ip not in self.history["completed"]:
                continue

            if self.can_run_completed(ip):

                self.device_tree.item(
                    item,
                    values=(
                        ip,
                        "↻ READY AGAIN"
                    )
                )

        self.root.after(
            60000,
            self.refresh_completed_statuses
        )

    # ========================================================
    # MÉTRICAS
    # ========================================================

    def update_metrics(self):

        self.metric_deleted.config(
            text=str(
                self.deleted_files
            )
        )

        self.metric_skipped.config(
            text=str(
                self.skipped_files
            )
        )

        self.metric_pending.config(
            text=str(
                len(
                    self.history[
                        "pending"
                    ]
                )
            )
        )

        self.metric_done.config(
            text=str(
                len(
                    self.history[
                        "completed"
                    ]
                )
            )
        )

    # ========================================================
    # FINALIZAR LIMPIEZA
    # ========================================================

    def clean_finished(self):

        self.cleaning = False

        self.set_controls(
            True
        )

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="● ONLINE",
            fg=GREEN
        )

        self.activity_label.config(
            text="✓",
            fg=GREEN
        )

        if self.stop_requested:

            self.operation_status.config(
                text="STOPPED"
            )

            self.log(
                "Operación detenida."
            )

        else:

            self.operation_status.config(
                text="COMPLETE"
            )

            self.log(
                "================================"
            )

            self.log(
                "OPERACIÓN FINALIZADA"
            )

            self.log(
                f"Equipos: "
                f"{self.processed_devices}/"
                f"{self.total_devices}"
            )

            self.log(
                f"Eliminados: "
                f"{self.deleted_files}"
            )

            self.log(
                f"Omitidos: "
                f"{self.skipped_files}"
            )

            self.log(
                f"Pendientes: "
                f"{len(self.history['pending'])}"
            )

            self.log(
                "================================"
            )

        self.refresh_pending()

        self.update_metrics()

        # Actualizar estados de equipos
        for item in self.device_tree.get_children():

            values = self.device_tree.item(
                item,
                "values"
            )

            if not values:
                continue

            ip = values[0]

            if ip in self.history["completed"]:

                self.device_tree.item(
                    item,
                    values=(
                        ip,
                        self.get_device_status(ip)
                    )
                )

    # ========================================================
    # STOP
    # ========================================================

    def stop_process(self):

        if not (
            self.scanning
            or self.cleaning
        ):

            return

        self.stop_requested = True

        self.status_label.config(
            text="● STOPPING",
            fg=YELLOW
        )

        self.operation_status.config(
            text="STOPPING..."
        )

        self.log(
            "Solicitud de detención enviada..."
        )

    # ========================================================
    # CONTROLES
    # ========================================================

    def set_controls(
        self,
        enabled
    ):

        state = (
            "normal"
            if enabled
            else "disabled"
        )

        self.scan_button.config(
            state=state
        )

        self.clean_selected_button.config(
            state=state
        )

        self.clean_pending_button.config(
            state=state
        )

        self.retry_button.config(
            state=state
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = DTRApp(
        root
    )

    root.mainloop()