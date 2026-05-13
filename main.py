import customtkinter as ctk
import os
import random
import csv
from datetime import datetime
from collections import deque
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(
    os.path.join(os.path.dirname(__file__), "mesa_sismica_theme.json")
)

# ── Configuración Global ──
FONT_NAME = "DejaVu Sans Mono"


# ═══════════════════════════════════════════════
# COMPONENTES ATÓMICOS
# ═══════════════════════════════════════════════


class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, label_text, placeholder_text="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.label.pack(anchor="w", padx=5)

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder_text,
            font=ctk.CTkFont(family=FONT_NAME, size=14),
            height=38,
        )
        self.entry.pack(fill="x", padx=5, pady=(4, 10))

    def get(self):
        return self.entry.get()


class LabeledOptionMenu(ctk.CTkFrame):
    def __init__(self, master, label_text, values, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.label.pack(anchor="w", padx=5)

        self.option_menu = ctk.CTkOptionMenu(
            self,
            values=values,
            font=ctk.CTkFont(family=FONT_NAME, size=13),
            height=38,
        )
        self.option_menu.pack(fill="x", padx=5, pady=(4, 10))

    def get(self):
        return self.option_menu.get()


class RadiobuttonList(ctk.CTkFrame):
    def __init__(self, master, label_text, options, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.label.pack(anchor="w", padx=5)

        self.value = ctk.StringVar(value=options[0])
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="x", padx=5, pady=5)

        for opt in options:
            rb = ctk.CTkRadioButton(
                self.container,
                text=opt,
                variable=self.value,
                value=opt,
                font=ctk.CTkFont(family=FONT_NAME, size=12),
            )
            rb.pack(side="left", padx=(0, 20))

    def get(self):
        return self.value.get()


# ═══════════════════════════════════════════════
# SECCIONES PRINCIPALES
# ═══════════════════════════════════════════════


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, theme_callback, **kwargs):
        super().__init__(master, corner_radius=20, height=80, **kwargs)
        self.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self,
            text="🔬 MESA SÍSMICA | Control de Laboratorio",
            font=ctk.CTkFont(family=FONT_NAME, size=24, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.title_label.pack(side="left", padx=30)

        self.status_indicator = ctk.CTkLabel(
            self,
            text="● DESCONECTADO",
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            text_color="#E74C3C",
        )
        self.status_indicator.pack(side="right", padx=30)
        # Theme toggle (switch elegante)
        self.theme_container = ctk.CTkFrame(self, fg_color="transparent")
        self.theme_container.pack(side="right", padx=(0, 15))

        self.sun_label = ctk.CTkLabel(
            self.theme_container, text="☀️", font=ctk.CTkFont(size=16),
        )
        self.sun_label.pack(side="left", padx=(0, 4))

        self.theme_switch = ctk.CTkSwitch(
            self.theme_container,
            text="",
            width=42,
            height=22,
            switch_width=38,
            switch_height=18,
            fg_color="#555555",
            progress_color="#00A8FF",
            button_color="white",
            button_hover_color="#E0E0E0",
            command=theme_callback,
        )
        self.theme_switch.select()  # Inicia en modo oscuro (ON)
        self.theme_switch.pack(side="left")

        self.moon_label = ctk.CTkLabel(
            self.theme_container, text="🌙", font=ctk.CTkFont(size=16),
        )
        self.moon_label.pack(side="left", padx=(4, 0))

    def set_status(self, text, color):
        self.status_indicator.configure(text=f"● {text}", text_color=color)


class ConfigSection(ctk.CTkFrame):
    def __init__(self, master, connect_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.connect_callback = connect_callback
        self.is_connected = False

        self.title = ctk.CTkLabel(
            self,
            text="📡 CONEXIÓN SERIAL",
            font=ctk.CTkFont(family=FONT_NAME, size=15, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.title.pack(anchor="w", padx=15, pady=(15, 10))

        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        self.controls.pack(fill="x", padx=15, pady=(0, 15))

        self.port_menu = ctk.CTkOptionMenu(
            self.controls,
            values=["COM1", "COM2", "COM3", "COM4", "/dev/ttyUSB0"],
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            height=35,
        )
        self.port_menu.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.connect_btn = ctk.CTkButton(
            self.controls,
            text="CONECTAR",
            width=120,
            height=35,
            font=ctk.CTkFont(family=FONT_NAME, size=12, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="black",
            command=self._handle_click,
        )
        self.connect_btn.pack(side="left", padx=(5, 0))

    def _handle_click(self):
        self.is_connected = not self.is_connected
        if self.is_connected:
            self.connect_btn.configure(
                text="DESCONECTAR",
                fg_color="#E74C3C",
                hover_color="#C0392B",
                text_color="white",
            )
        else:
            self.connect_btn.configure(
                text="CONECTAR",
                fg_color="#2ECC71",
                hover_color="#27AE60",
                text_color="black",
            )
        self.connect_callback(self.is_connected, self.port_menu.get())


class FormParams(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.title = ctk.CTkLabel(
            self,
            text="⚙️ PARÁMETROS DE ENSAYO",
            font=ctk.CTkFont(family=FONT_NAME, size=15, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.title.pack(anchor="w", padx=15, pady=(15, 10))

        self.mode = LabeledOptionMenu(
            self,
            "Modo de Operación:",
            [
                "Onda Senoidal",
                "Barrido de Frecuencia",
                "Pulso Único",
                "Tren de pulsos",
                "Calibración",
            ],
        )
        self.mode.pack(fill="x", padx=15)

        self.freq = LabeledEntry(self, "Frecuencia (Hz):", "2.0")
        self.freq.pack(fill="x", padx=15)

        self.time = LabeledEntry(self, "Tiempo de Ensayo (s):", "30")
        self.time.pack(fill="x", padx=15)

        self.reps = LabeledEntry(self, "Amplitud (G):", "1.0")
        self.reps.pack(fill="x", padx=15)

        self.direction = RadiobuttonList(
            self, "Dirección Inicial:", ["Derecha", "Izquierda"]
        )
        self.direction.pack(fill="x", padx=15, pady=(5, 15))

    def get_params(self):
        try:
            return {
                "modo": self.mode.get(),
                "frecuencia": float(self.freq.get() or 2.0),
                "tiempo": float(self.time.get() or 30),
                "amplitud": float(self.reps.get() or 1.0),
                "direccion": self.direction.get(),
            }
        except ValueError:
            return None


class ActionPanel(ctk.CTkFrame):
    def __init__(
        self, master, start_callback, stop_callback, export_callback, **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.start_btn = ctk.CTkButton(
            self,
            text="▶ INICIAR ENSAYO",
            font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold"),
            height=50,
            fg_color="#00A8FF",
            hover_color="#0080CC",
            text_color="black",
            command=start_callback,
        )
        self.start_btn.pack(fill="x", pady=(0, 10))

        self.stop_btn = ctk.CTkButton(
            self,
            text="⏹ PARADA DE EMERGENCIA",
            font=ctk.CTkFont(family=FONT_NAME, size=16, weight="bold"),
            height=50,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=stop_callback,
        )
        self.stop_btn.pack(fill="x", pady=(0, 10))

        self.export_btn = ctk.CTkButton(
            self,
            text="💾 EXPORTAR DATOS (.CSV)",
            font=ctk.CTkFont(family=FONT_NAME, size=13, weight="bold"),
            height=40,
            fg_color="#F39C12",
            hover_color="#D35400",
            text_color="black",
            command=export_callback,
        )
        self.export_btn.pack(fill="x")


class GraphSection(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.title = ctk.CTkLabel(
            self,
            text="📈 GRÁFICAS DE TELEMETRÍA (MPU6050)",
            font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.title.pack(anchor="w", padx=15, pady=(15, 5))

        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor("#131920")
        self.ax.set_facecolor("#0A0E14")

        self.ax.tick_params(colors="#7A8CA3", labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color("#2A3A4E")

        self.ax.set_ylim(-15, 15)
        self.ax.grid(True, color="#1A2332", linestyle="--")

        self.max_points = 100
        self.data_x = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.data_y = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.data_z = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.time_buffer = np.linspace(0, self.max_points, self.max_points)

        (self.line_x,) = self.ax.plot(
            self.time_buffer, self.data_x, label="Acc X", color="#FF3E3E", linewidth=1.5
        )
        (self.line_y,) = self.ax.plot(
            self.time_buffer, self.data_y, label="Acc Y", color="#3EBCFF", linewidth=1.5
        )
        (self.line_z,) = self.ax.plot(
            self.time_buffer, self.data_z, label="Acc Z", color="#3EFF3E", linewidth=1.5
        )

        self.ax.legend(
            loc="upper right",
            fontsize=7,
            facecolor="#131920",
            edgecolor="#2A3A4E",
            labelcolor="white",
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def update_graph(self, x, y, z):
        self.data_x.append(x)
        self.data_y.append(y)
        self.data_z.append(z)
        self.line_x.set_ydata(self.data_x)
        self.line_y.set_ydata(self.data_y)
        self.line_z.set_ydata(self.data_z)
        self.canvas.draw_idle()

    def clear_graph(self):
        for _ in range(self.max_points):
            self.data_x.append(0.0)
            self.data_y.append(0.0)
            self.data_z.append(0.0)
        self.update_graph(0, 0, 0)


class LogMonitor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.title = ctk.CTkLabel(
            self,
            text="🖥️ MONITOR DE ESTADO",
            font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
            text_color=("#0070CC", "#00A8FF"),
        )
        self.title.pack(anchor="w", padx=15, pady=(15, 5))

        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family=FONT_NAME, size=12),
            fg_color=("#FFFFFF", "#0A0E14"),
            border_width=2,
            border_color=("#9BA8BE", "#2A3A4E"),
        )
        self.textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log("Sistema inicializado. Esperando conexión serial.")

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.textbox.insert("end", f"[{now}] {message}\n")
        self.textbox.see("end")


class FooterFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=10, height=50, **kwargs)
        self.pack_propagate(False)

        self.info = ctk.CTkLabel(
            self,
            text="Universidad Cooperativa de Colombia | Luis Mateo Nieto Vargas © 2026",
            font=ctk.CTkFont(family=FONT_NAME, size=11),
            text_color="gray",
        )
        self.info.pack(expand=True)


# ═══════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mesa Sísmica - Software de Control")
        self.geometry("1400x900")
        self.minsize(1000, 700)

        self.is_connected = False
        self.is_running = False
        self.trial_data = []  # Para exportar
        self.start_time = 0
        self.current_params = None

        self._layout()

    def _layout(self):
        self.header = HeaderFrame(self, self.toggle_theme)
        self.header.pack(side="top", fill="x", padx=20, pady=(20, 10))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.left_column = ctk.CTkFrame(
            self.main_container, fg_color="transparent", width=450
        )
        self.left_column.pack(side="left", fill="both", padx=(0, 10))
        self.left_column.pack_propagate(False)

        self.config_box = ConfigSection(self.left_column, self.on_serial_toggle)
        self.config_box.pack(fill="x", pady=(0, 10))

        self.params_box = FormParams(self.left_column)
        self.params_box.pack(fill="both", expand=True, pady=(0, 10))

        self.action_box = ActionPanel(
            self.left_column, self.on_start, self.on_stop, self.on_export
        )
        self.action_box.pack(fill="x")

        self.right_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_column.pack(side="left", fill="both", expand=True)

        self.right_column.grid_rowconfigure(0, weight=3)
        self.right_column.grid_rowconfigure(1, weight=1)
        self.right_column.grid_columnconfigure(0, weight=1)

        self.graph_box = GraphSection(self.right_column)
        self.graph_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.monitor_box = LogMonitor(self.right_column)
        self.monitor_box.grid(row=1, column=0, sticky="nsew")

        self.footer = FooterFrame(self)
        self.footer.pack(side="bottom", fill="x", padx=20, pady=(10, 20))

    def on_serial_toggle(self, connected, port):
        self.is_connected = connected
        if connected:
            self.header.set_status(f"CONECTADO - {port}", "#2ECC71")
            self.monitor_box.log(f"Conexión establecida exitosamente.")
        else:
            self.header.set_status("DESCONECTADO", "#E74C3C")
            self.monitor_box.log("Puerto serial cerrado.")
            if self.is_running:
                self.on_stop()

    def on_start(self):
        if not self.is_connected:
            self.monitor_box.log("ERROR: Se requiere conexión serial.")
            return

        self.current_params = self.params_box.get_params()
        if not self.current_params:
            self.monitor_box.log("ERROR: Parámetros inválidos.")
            return

        self.is_running = True
        self.trial_data = []
        self.start_time = datetime.now().timestamp()

        # Estado del filtro IIR (memoria de muestras previas por eje)
        self._prev_x = [0.0, 0.0]
        self._prev_y = [0.0, 0.0]
        self._prev_z = [0.0, 0.0]
        self._peak_x = 0.0

        self.header.set_status("ENSAYO EN CURSO", "#00A8FF")
        self.monitor_box.log(
            f"Iniciando Sismo Sintético: {self.current_params['tiempo']}s"
        )
        self._simulate_loop()

    def on_stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self.header.set_status("CONECTADO", "#2ECC71")
        self.monitor_box.log(
            f"Ensayo finalizado. Puntos capturados: {len(self.trial_data)}"
        )
        self.graph_box.clear_graph()

    def on_export(self):
        if not self.trial_data:
            messagebox.showwarning(
                "Exportar", "No hay datos para exportar. Inicie un ensayo primero."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar Datos de Ensayo",
            initialfile=f"ensayo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if file_path:
            try:
                with open(file_path, mode="w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Tiempo (s)", "Acc X (G)", "Acc Y (G)", "Acc Z (G)"]
                    )
                    writer.writerows(self.trial_data)
                self.monitor_box.log(
                    f"Datos exportados a: {os.path.basename(file_path)}"
                )
                messagebox.showinfo("Exportar", "Datos exportados correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def _iir_filter(self, raw, prev, alpha=0.35):
        """Filtro IIR paso-bajo de 2do orden. Suaviza ruido blanco para
        darle la 'forma' de frecuencia de un sismo real sin hacerlo periódico."""
        out = alpha * raw + (1 - alpha) * prev[0] + 0.15 * (prev[0] - prev[1])
        prev[1] = prev[0]
        prev[0] = out
        return out

    def _saragoni_hart_envelope(self, t, T):
        """Envolvente de Saragoni-Hart: e(t) = a * t^b * exp(-c*t).
        Modela la forma temporal de un sismo real con subida rápida
        y decaimiento exponencial largo (coda sísmica)."""
        # Normalizar t al rango [0, 1]
        tn = t / T
        # Parámetros ajustados para un sismo típico
        b = 2.0
        c = 5.0
        # Calcular y normalizar para que el pico sea ~1.0
        peak_time = b / c
        peak_val = (peak_time ** b) * math.exp(-c * peak_time)
        if peak_val == 0:
            return 0.0
        env = ((tn ** b) * math.exp(-c * tn)) / peak_val
        return min(env, 1.0)

    def _simulate_loop(self):
        if not self.is_running:
            return

        t = datetime.now().timestamp() - self.start_time
        T = self.current_params["tiempo"]
        amp_max = self.current_params["amplitud"]

        # 1. Envolvente Saragoni-Hart (forma real de un sismo)
        envelope = self._saragoni_hart_envelope(t, T)

        # 2. Ruido blanco gaussiano (la BASE de un sismo real, NO sinusoides)
        raw_x = random.normalvariate(0, 1.0)
        raw_y = random.normalvariate(0, 0.6)
        raw_z = random.normalvariate(0, 0.3)

        # 3. Filtro IIR (simula el contenido frecuencial del suelo,
        #    elimina las frecuencias muy altas dejando la 'textura' sísmica)
        filtered_x = self._iir_filter(raw_x, self._prev_x, alpha=0.45)
        filtered_y = self._iir_filter(raw_y, self._prev_y, alpha=0.40)
        filtered_z = self._iir_filter(raw_z, self._prev_z, alpha=0.30)

        # 4. Resultado: Ruido filtrado × Envolvente × Amplitud
        ax_x = filtered_x * envelope * amp_max * 8.0
        ax_y = filtered_y * envelope * amp_max * 4.0
        ax_z = 9.8 + (filtered_z * envelope * amp_max * 0.5)

        # Rastrear pico máximo
        if abs(ax_x) > abs(self._peak_x):
            self._peak_x = ax_x

        # Guardar datos
        self.trial_data.append(
            [round(t, 3), round(ax_x, 3), round(ax_y, 3), round(ax_z, 3)]
        )

        # Actualizar UI
        self.graph_box.update_graph(ax_x, ax_y, ax_z)

        # Monitor de estado
        if len(self.trial_data) % 25 == 0:
            self.monitor_box.log(
                f"Env: {envelope*100:.0f}% | X={ax_x:+.2f}G | PGA={self._peak_x:.2f}G"
            )

        # Verificar tiempo límite
        if t >= T:
            self.on_stop()
        else:
            self.after(40, self._simulate_loop)  # ~25 Hz

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        is_dark = current == "Dark"
        new_mode = "Light" if is_dark else "Dark"
        ctk.set_appearance_mode(new_mode)

        # Actualizar colores del gráfico Matplotlib
        if new_mode == "Dark":
            bg_fig, bg_ax = "#131920", "#0A0E14"
            grid_color, spine_color = "#1A2332", "#2A3A4E"
            tick_color, legend_bg = "#7A8CA3", "#131920"
        else:
            bg_fig, bg_ax = "#F5F5F5", "#FFFFFF"
            grid_color, spine_color = "#D0D0D0", "#AAAAAA"
            tick_color, legend_bg = "#333333", "#F5F5F5"

        ax = self.graph_box.ax
        fig = self.graph_box.fig
        fig.patch.set_facecolor(bg_fig)
        ax.set_facecolor(bg_ax)
        ax.tick_params(colors=tick_color)
        for spine in ax.spines.values():
            spine.set_color(spine_color)
        ax.grid(True, color=grid_color, linestyle="--")
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(legend_bg)
            legend.get_frame().set_edgecolor(spine_color)
            for text in legend.get_texts():
                text.set_color("white" if new_mode == "Dark" else "#333333")
        self.graph_box.canvas.draw_idle()


if __name__ == "__main__":
    app = App()
    app.mainloop()
