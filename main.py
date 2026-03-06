import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import os
import sys
from PIL import Image, ImageTk

# === FUNCIÓN PARA COMPATIBILIDAD CON .EXE ===
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class BuscadorDiagnosticos:
    def __init__(self, parent):
        self.parent = parent
        self.diagnosticos = []
        self.cargar_diagnosticos()
        self.crear_ventana()

    def cargar_diagnosticos(self):
        """Carga la base de datos de diagnósticos desde JSON"""
        try:
            # Intentar cargar desde diagnosticos1.json primero
            diagnosticos1_path = resource_path('diagnosticos1.json')
            diagnosticos_path = resource_path('diagnosticos.json')
            
            if os.path.exists(diagnosticos1_path):
                with open(diagnosticos1_path, 'r', encoding='utf-8') as f:
                    self.diagnosticos = json.load(f)
                print(f"Diagnósticos cargados desde diagnosticos1.json: {len(self.diagnosticos)}")
            elif os.path.exists(diagnosticos_path):
                with open(diagnosticos_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.diagnosticos = data.get('diagnosticos', [])
                print(f"Diagnósticos cargados desde diagnosticos.json: {len(self.diagnosticos)}")
            else:
                print("No se encontró archivo de diagnósticos")
                self.diagnosticos = []
        except Exception as e:
            print(f"Error cargando diagnósticos: {e}")
            self.diagnosticos = []

    def crear_ventana(self):
        """Crea la ventana del buscador de diagnósticos"""
        self.ventana = tk.Toplevel(self.parent.root)
        self.ventana.title("Buscador de Diagnósticos CIE-10")
        self.ventana.geometry("900x600")
        self.ventana.configure(bg='white')

        # Frame de búsqueda
        frame_busqueda = ttk.Frame(self.ventana)
        frame_busqueda.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame_busqueda, text="🔍 Buscar por código o descripción:",
                  font=("Arial", 10, "bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.entry_busqueda = ttk.Entry(frame_busqueda, width=50, font=("Arial", 10))
        self.entry_busqueda.grid(row=0, column=1, padx=(0, 10))
        self.entry_busqueda.bind('<KeyRelease>', self.filtrar_diagnosticos)
        self.entry_busqueda.focus()

        ttk.Button(frame_busqueda, text="Buscar",
                  command=self.filtrar_diagnosticos).grid(row=0, column=2, padx=(0, 10))

        ttk.Button(frame_busqueda, text="Limpiar",
                  command=self.limpiar_busqueda).grid(row=0, column=3)

        # Label de resultados
        self.label_resultados = ttk.Label(frame_busqueda, text="", font=("Arial", 9))
        self.label_resultados.grid(row=1, column=0, columnspan=4, pady=(5, 0), sticky="w")

        # Frame de resultados
        frame_resultados = ttk.Frame(self.ventana)
        frame_resultados.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview para mostrar resultados
        columns = ('Código', 'Nombre', 'Descripción')
        self.tree = ttk.Treeview(frame_resultados, columns=columns, show='headings', height=20)

        # Configurar columnas
        self.tree.heading('Código', text='Código')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Descripción', text='Descripción')
        self.tree.column('Código', width=80)
        self.tree.column('Nombre', width=450)
        self.tree.column('Descripción', width=300)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_resultados, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Doble click para seleccionar
        self.tree.bind('<Double-1>', self.seleccionar_diagnostico)

        # Frame de botones
        frame_botones = ttk.Frame(self.ventana)
        frame_botones.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(frame_botones, text="Seleccionar",
                  command=lambda: self.seleccionar_diagnostico(None)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botones, text="Cancelar",
                  command=self.ventana.destroy).pack(side=tk.RIGHT)

        # Cargar todos los diagnósticos inicialmente (limitados)
        self.mostrar_diagnosticos(self.diagnosticos[:50])
        self.label_resultados.config(text=f"Mostrando primeros 50 de {len(self.diagnosticos)} diagnósticos. Use el buscador para filtrar.")

    def filtrar_diagnosticos(self, event=None):
        """Filtra los diagnósticos según el texto de búsqueda"""
        texto_busqueda = self.entry_busqueda.get().lower().strip()

        if not texto_busqueda:
            self.mostrar_diagnosticos(self.diagnosticos[:50])
            self.label_resultados.config(text=f"Mostrando primeros 50 de {len(self.diagnosticos)} diagnósticos. Use el buscador para filtrar.")
            return

        resultados = []
        for diagnostico in self.diagnosticos:
            codigo = diagnostico.get('Codigo', '').lower()
            nombre = diagnostico.get('Nombre', '').lower()
            descripcion = diagnostico.get('Descripcion', '').lower()

            # Buscar en cualquiera de los campos
            if (texto_busqueda in codigo or
                texto_busqueda in nombre or
                texto_busqueda in descripcion or
                any(palabra in nombre for palabra in texto_busqueda.split()) or
                any(palabra in descripcion for palabra in texto_busqueda.split())):
                resultados.append(diagnostico)

        self.mostrar_diagnosticos(resultados[:100])  # Limitar a 100 resultados
        self.label_resultados.config(text=f"Encontrados: {len(resultados)} diagnósticos (mostrando los primeros 100)")

    def mostrar_diagnosticos(self, diagnosticos):
        """Muestra los diagnósticos en el treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for diagnostico in diagnosticos:
            self.tree.insert('', tk.END,
                             values=(diagnostico.get('Codigo', ''),
                                     diagnostico.get('Nombre', ''),
                                     diagnostico.get('Descripcion', '')))

    def limpiar_busqueda(self):
        """Limpia la búsqueda y muestra los primeros diagnósticos"""
        self.entry_busqueda.delete(0, tk.END)
        self.mostrar_diagnosticos(self.diagnosticos[:50])
        self.label_resultados.config(text=f"Mostrando primeros 50 de {len(self.diagnosticos)} diagnósticos. Use el buscador para filtrar.")

    def seleccionar_diagnostico(self, event):
        """Selecciona un diagnóstico y cierra la ventana"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un diagnóstico")
            return

        item = self.tree.item(seleccion[0])
        codigo, nombre, descripcion = item['values']

        # Insertar en el campo de diagnóstico
        if hasattr(self.parent, 'diagnostico'):
            self.parent.diagnostico.delete("1.0", tk.END)
            # Formato: Código - Nombre
            texto_diagnostico = f"{codigo} - {nombre}"
            self.parent.diagnostico.insert("1.0", texto_diagnostico)

        self.ventana.destroy()

class GeneradorHistoriaClinica:
    def __init__(self, root):
        self.root = root
        self.root.title("CliniSoft")
        self.diagnosticos = []
        self.cargar_diagnosticos()

        # Datos compartidos
        self.datos_shared = {}
        self.current_mode = "Historia Clinica"

        # Obtener dimensiones de la pantalla
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Configurar ventana al 90% del tamaño de la pantalla
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)

        # Centrar la ventana
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='white')

        # Cargar imágenes una sola vez
        self.cargar_imagenes()

        self.crear_interfaz()

    def cargar_imagenes(self):
        """Carga las imágenes una vez para reutilizarlas"""
        try:
            # Cargar logo principal - USA resource_path
            logo_path = resource_path('FullLogo_Transparent.png')
            if os.path.exists(logo_path):
                pil_image = Image.open(logo_path)
                max_height = 100
                pil_image.thumbnail((200, max_height), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(pil_image)
            else:
                self.logo_image = None
                print(f"No se encontró el logo principal en: {logo_path}")

            # Cargar imagen de firma - USA resource_path
            firma_path = resource_path('firma.png')
            if os.path.exists(firma_path):
                firma_image = Image.open(firma_path)
                firma_image.thumbnail((250, 100), Image.Resampling.LANCZOS)
                self.firma_image = ImageTk.PhotoImage(firma_image)
            else:
                self.firma_image = None
                print(f"No se encontró la imagen de firma en: {firma_path}")

        except Exception as e:
            print(f"Error cargando imágenes: {e}")
            self.logo_image = None
            self.firma_image = None

    def cargar_diagnosticos(self):
        """Carga la base de datos de diagnósticos desde JSON"""
        try:
            # Intentar cargar desde diagnosticos1.json primero - USA resource_path
            diagnosticos1_path = resource_path('diagnosticos1.json')
            diagnosticos_path = resource_path('diagnosticos.json')
            
            if os.path.exists(diagnosticos1_path):
                with open(diagnosticos1_path, 'r', encoding='utf-8') as f:
                    self.diagnosticos = json.load(f)
                print(f"Diagnósticos cargados desde diagnosticos1.json: {len(self.diagnosticos)}")
            elif os.path.exists(diagnosticos_path):
                with open(diagnosticos_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.diagnosticos = data.get('diagnosticos', [])
                print(f"Diagnósticos cargados desde diagnosticos.json: {len(self.diagnosticos)}")
            else:
                self.crear_diagnosticos_base()
        except Exception as e:
            print(f"Error cargando diagnósticos: {e}")
            self.diagnosticos = []

    def crear_diagnosticos_base(self):
        """Crea un archivo base de diagnósticos si no existe"""
        diagnosticos_base = {
            "diagnosticos": [
                {"codigo": "A00", "descripcion": "Cólera"},
                {"codigo": "A01", "descripcion": "Fiebres tifoidea y paratifoidea"},
                {"codigo": "A09", "descripcion": "Diarrea y gastroenteritis de presunto origen infeccioso"},
                {"codigo": "I10", "descripcion": "Hipertensión esencial (primaria)"},
                {"codigo": "E11", "descripcion": "Diabetes mellitus tipo 2"},
                {"codigo": "J45", "descripcion": "Asma"},
                {"codigo": "J06.9", "descripcion": "Infección aguda de las vías respiratorias superiores"},
                {"codigo": "M54.5", "descripcion": "Lumbalgia"},
                {"codigo": "R10.4", "descripcion": "Dolor abdominal"},
                {"codigo": "Z00.0", "descripcion": "Examen general de salud"}
            ]
        }
        with open('diagnosticos.json', 'w', encoding='utf-8') as f:
            json.dump(diagnosticos_base, f, ensure_ascii=False, indent=2)
        self.diagnosticos = diagnosticos_base['diagnosticos']
        print("Archivo diagnosticos.json creado")

    def crear_interfaz(self):
        """Crea la interfaz gráfica principal con selector"""
        # Frame principal
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Selector de modo
        selector_frame = ttk.Frame(main_container)
        selector_frame.pack(fill=tk.X, pady=10)

        ttk.Label(selector_frame, text="Seleccionar Apartado:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)

        self.modo_selector = ttk.Combobox(selector_frame, values=["Historia Clinica", "Formula Medica", "Evolucion Medica"], state="readonly")
        self.modo_selector.current(0)
        self.modo_selector.pack(side=tk.LEFT, padx=10)
        self.modo_selector.bind("<<ComboboxSelected>>", self.cambiar_modo)

        # Contenedor para los frames de modos
        self.content_container = ttk.Frame(main_container)
        self.content_container.pack(fill=tk.BOTH, expand=True)

        # Crear frames para cada modo
        self.historia_frame = ttk.Frame(self.content_container)
        self.formula_frame = ttk.Frame(self.content_container)
        self.evolucion_frame = ttk.Frame(self.content_container)

        self.crear_historia_frame(self.historia_frame)
        self.crear_formula_frame(self.formula_frame)
        self.crear_evolucion_frame(self.evolucion_frame)

        # Mostrar el frame inicial
        self.historia_frame.pack(fill=tk.BOTH, expand=True)

    def cambiar_modo(self, event):
        modo = self.modo_selector.get()
        if modo == self.current_mode:
            return

        # Ocultar frame actual
        if self.current_mode == "Historia Clinica":
            self.historia_frame.pack_forget()
            self.actualizar_shared_from_historia()
        elif self.current_mode == "Formula Medica":
            self.formula_frame.pack_forget()
            self.actualizar_shared_from_formula()
        elif self.current_mode == "Evolucion Medica":
            self.evolucion_frame.pack_forget()
            self.actualizar_shared_from_evolucion()

        # Mostrar nuevo frame y actualizar datos
        self.current_mode = modo
        if modo == "Historia Clinica":
            self.actualizar_historia_from_shared()
            self.historia_frame.pack(fill=tk.BOTH, expand=True)
        elif modo == "Formula Medica":
            self.actualizar_formula_from_shared()
            self.formula_frame.pack(fill=tk.BOTH, expand=True)
        elif modo == "Evolucion Medica":
            self.actualizar_evolucion_from_shared()
            self.evolucion_frame.pack(fill=tk.BOTH, expand=True)

    def crear_scrollable_frame(self, parent):
        """Crea un frame scrollable para cada modo"""
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Frame interno centrado
        centered_frame = ttk.Frame(scrollable_frame)
        centered_frame.pack(padx=50, pady=20, fill=tk.BOTH, expand=True)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return centered_frame

    def crear_historia_frame(self, parent):
        centered_frame = self.crear_scrollable_frame(parent)
        self.crear_titulo(centered_frame, "HISTORIA CLINICA")
        self.crear_encabezado(centered_frame, prefix="hist_")
        self.crear_datos_paciente(centered_frame, prefix="hist_")
        self.crear_motivo_consulta(centered_frame)
        self.crear_enfermedad_actual(centered_frame)
        self.crear_antecedentes(centered_frame)
        self.crear_examen_fisico(centered_frame)
        self.crear_diagnostico(centered_frame)
        self.crear_conducta(centered_frame)
        self.crear_datos_medico(centered_frame, prefix="hist_")
        self.crear_botones(centered_frame)

    def crear_formula_frame(self, parent):
        centered_frame = self.crear_scrollable_frame(parent)
        self.crear_titulo(centered_frame, "FORMULA MEDICA")
        self.crear_encabezado(centered_frame, prefix="form_")
        self.crear_datos_paciente(centered_frame, prefix="form_")
        self.crear_formula_medica(centered_frame)
        self.crear_datos_medico(centered_frame, prefix="form_")
        self.crear_botones(centered_frame)

    def crear_evolucion_frame(self, parent):
        centered_frame = self.crear_scrollable_frame(parent)
        self.crear_titulo(centered_frame, "EVOLUCION MEDICA")
        self.crear_encabezado(centered_frame, prefix="evol_")
        self.crear_datos_paciente(centered_frame, prefix="evol_")
        self.crear_evolucion_medica(centered_frame)
        self.crear_datos_medico(centered_frame, prefix="evol_")
        self.crear_botones(centered_frame)

    def crear_titulo(self, parent, texto_titulo):
        """Crea el título principal con logo"""
        titulo_frame = ttk.Frame(parent)
        titulo_frame.pack(fill=tk.X, pady=(0, 15))

        # Mostrar el logo (ya cargado previamente)
        if hasattr(self, 'logo_image') and self.logo_image:
            logo_label = tk.Label(titulo_frame, image=self.logo_image, bg='white')
            logo_label.pack(side=tk.LEFT, padx=(0, 20))
        else:
            empty_label = tk.Label(titulo_frame, text="", bg='white', width=10)
            empty_label.pack(side=tk.LEFT, padx=(0, 20))

        # Frame para el texto del título
        texto_frame = ttk.Frame(titulo_frame)
        texto_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl_titulo = tk.Label(texto_frame,
                              text=texto_titulo,
                              font=("Arial", 18, "bold"),
                              bg='white',
                              fg='navy')
        lbl_titulo.pack(pady=5)

        lbl_subtitulo = tk.Label(texto_frame,
                                 text="MEDICO INTERNISTA UNIVERSIDAD DE ZULIA",
                                 font=("Arial", 14, "bold"),
                                 bg='white',
                                 fg='black')
        lbl_subtitulo.pack(pady=2)

    def crear_encabezado(self, parent, prefix=""):
        """Crea la sección de encabezado"""
        frame = ttk.LabelFrame(parent, text="", padding=15)
        frame.pack(fill=tk.X, pady=8)

        ahora = datetime.now()

        row = 0
        ttk.Label(frame, text="FECHA", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(frame, text="HORA", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)

        row += 1
        fecha_frame = ttk.Frame(frame)
        fecha_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        setattr(self, f'{prefix}fecha_dia', ttk.Entry(fecha_frame, width=4, justify='center', font=("Arial", 11)))
        dia = getattr(self, f'{prefix}fecha_dia')
        dia.insert(0, ahora.strftime("%d"))
        dia.pack(side=tk.LEFT)
        dia.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'fecha_dia', dia.get()))

        ttk.Label(fecha_frame, text="/", font=("Arial", 11)).pack(side=tk.LEFT)
        setattr(self, f'{prefix}fecha_mes', ttk.Entry(fecha_frame, width=4, justify='center', font=("Arial", 11)))
        mes = getattr(self, f'{prefix}fecha_mes')
        mes.insert(0, ahora.strftime("%m"))
        mes.pack(side=tk.LEFT)
        mes.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'fecha_mes', mes.get()))

        ttk.Label(fecha_frame, text="/", font=("Arial", 11)).pack(side=tk.LEFT)
        setattr(self, f'{prefix}fecha_anio', ttk.Entry(fecha_frame, width=6, justify='center', font=("Arial", 11)))
        anio = getattr(self, f'{prefix}fecha_anio')
        anio.insert(0, ahora.strftime("%Y"))
        anio.pack(side=tk.LEFT)
        anio.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'fecha_anio', anio.get()))

        setattr(self, f'{prefix}hora', ttk.Entry(frame, width=12, justify='center', font=("Arial", 11)))
        hora = getattr(self, f'{prefix}hora')
        hora.insert(0, ahora.strftime("%H:%M"))
        hora.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        hora.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'hora', hora.get()))

        for i in range(4):
            frame.columnconfigure(i, weight=1)

    def crear_datos_paciente(self, parent, prefix=""):
        """Crea la sección de datos del paciente"""
        frame = ttk.LabelFrame(parent, text="DATOS DEL PACIENTE", padding=15)
        frame.pack(fill=tk.X, pady=8)

        row = 0
        ttk.Label(frame, text="NOMBRE", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(frame, text="EDAD", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(frame, text="SEXO", font=("Arial", 10, "bold")).grid(row=row, column=2, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}nombre_paciente', ttk.Entry(frame, width=45, font=("Arial", 11)))
        nombre = getattr(self, f'{prefix}nombre_paciente')
        nombre.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        nombre.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'nombre_paciente', nombre.get()))

        setattr(self, f'{prefix}edad_paciente', ttk.Entry(frame, width=12, font=("Arial", 11)))
        edad = getattr(self, f'{prefix}edad_paciente')
        edad.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        edad.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'edad_paciente', edad.get()))

        setattr(self, f'{prefix}sexo_paciente', ttk.Combobox(frame, width=10, values=["M", "F", "OTRO"], font=("Arial", 11)))
        sexo = getattr(self, f'{prefix}sexo_paciente')
        sexo.grid(row=row, column=2, sticky="ew", padx=5, pady=5)
        sexo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_shared(prefix + 'sexo_paciente', sexo.get()))

        row += 1
        ttk.Label(frame, text="TIPO DOCUMENTO", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(frame, text="No. DOCUMENTO IDENTIDAD", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(frame, text="TIPO AFILIADO", font=("Arial", 10, "bold")).grid(row=row, column=2, sticky="w", padx=5)
        ttk.Label(frame, text="OCUPACION", font=("Arial", 10, "bold")).grid(row=row, column=3, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}tipo_documento_paciente', ttk.Combobox(frame, width=15, values=["C.C.", "T.I.", "C.E.", "RC", "NU"], font=("Arial", 11)))
        tipo_doc = getattr(self, f'{prefix}tipo_documento_paciente')
        tipo_doc.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        tipo_doc.bind('<<ComboboxSelected>>', lambda e: self.actualizar_shared(prefix + 'tipo_documento_paciente', tipo_doc.get()))

        setattr(self, f'{prefix}documento_paciente', ttk.Entry(frame, width=22, font=("Arial", 11)))
        doc = getattr(self, f'{prefix}documento_paciente')
        doc.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        doc.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'documento_paciente', doc.get()))

        tipo_afil_frame = ttk.Frame(frame)
        tipo_afil_frame.grid(row=row, column=2, sticky="ew", padx=5, pady=5)
        setattr(self, f'{prefix}tipo_afiliado_cotiz', ttk.Combobox(tipo_afil_frame, width=10, values=["COTIZ", "BENEF"], font=("Arial", 11)))
        tipo_afil = getattr(self, f'{prefix}tipo_afiliado_cotiz')
        tipo_afil.pack(side=tk.LEFT, padx=2)
        tipo_afil.bind('<<ComboboxSelected>>', lambda e: self.actualizar_shared(prefix + 'tipo_afiliado_cotiz', tipo_afil.get()))

        setattr(self, f'{prefix}ocupacion_paciente', ttk.Entry(frame, width=18, font=("Arial", 11)))
        ocup = getattr(self, f'{prefix}ocupacion_paciente')
        ocup.grid(row=row, column=3, sticky="ew", padx=5, pady=5)
        ocup.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'ocupacion_paciente', ocup.get()))

        row += 1
        ttk.Label(frame, text="ESTADO CIVIL", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(frame, text="DIRECCIÓN RESIDENCIA", font=("Arial", 10, "bold")).grid(row=row, column=1, columnspan=2, sticky="w", padx=5)
        ttk.Label(frame, text="TELEFONO", font=("Arial", 10, "bold")).grid(row=row, column=3, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}estado_civil', ttk.Combobox(frame, width=15, values=["SOLTERO", "CASADO", "UNION LIBRE", "DIVORCIADO", "VIUDO"], font=("Arial", 11)))
        est_civ = getattr(self, f'{prefix}estado_civil')
        est_civ.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        est_civ.bind('<<ComboboxSelected>>', lambda e: self.actualizar_shared(prefix + 'estado_civil', est_civ.get()))

        setattr(self, f'{prefix}direccion_paciente', ttk.Entry(frame, width=45, font=("Arial", 11)))
        dir_pac = getattr(self, f'{prefix}direccion_paciente')
        dir_pac.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        dir_pac.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'direccion_paciente', dir_pac.get()))

        setattr(self, f'{prefix}telefono_paciente', ttk.Entry(frame, width=18, font=("Arial", 11)))
        tel = getattr(self, f'{prefix}telefono_paciente')
        tel.grid(row=row, column=3, sticky="ew", padx=5, pady=5)
        tel.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'telefono_paciente', tel.get()))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)

    def crear_motivo_consulta(self, parent):
        """Crea la sección de motivo de consulta"""
        frame = ttk.LabelFrame(parent, text="MOTIVO DE CONSULTA", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.motivo_consulta = tk.Text(frame, height=4, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.motivo_consulta.yview)
        self.motivo_consulta.configure(yscrollcommand=scrollbar.set)

        self.motivo_consulta.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def crear_enfermedad_actual(self, parent):
        """Crea la sección de enfermedad actual"""
        frame = ttk.LabelFrame(parent, text="ENFERMEDAD ACTUAL", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.enfermedad_actual = tk.Text(frame, height=5, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.enfermedad_actual.yview)
        self.enfermedad_actual.configure(yscrollcommand=scrollbar.set)

        self.enfermedad_actual.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def crear_antecedentes(self, parent):
        """Crea la sección de antecedentes"""
        frame = ttk.LabelFrame(parent, text="ANTECEDENTES", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.antecedentes = tk.Text(frame, height=5, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.antecedentes.yview)
        self.antecedentes.configure(yscrollcommand=scrollbar.set)

        self.antecedentes.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def calcular_imc(self, prefix=""):
        """Calcula el IMC automáticamente"""
        try:
            peso = getattr(self, f'{prefix}peso').get().strip()
            talla = getattr(self, f'{prefix}talla').get().strip()

            if peso and talla:
                peso_val = float(peso)
                talla_val = float(talla) / 100
                if talla_val > 0:
                    imc = peso_val / (talla_val ** 2)
                    getattr(self, f'{prefix}imc_var').set(f"{imc:.1f}")

                    if imc < 18.5:
                        clas = "Bajo peso"
                    elif imc < 25:
                        clas = "Normal"
                    elif imc < 30:
                        clas = "Sobrepeso"
                    elif imc < 35:
                        clas = "Obesidad I"
                    elif imc < 40:
                        clas = "Obesidad II"
                    else:
                        clas = "Obesidad III"
                    getattr(self, f'{prefix}imc_clasificacion_var').set(clas)
                else:
                    getattr(self, f'{prefix}imc_var').set("")
                    getattr(self, f'{prefix}imc_clasificacion_var').set("")
            else:
                getattr(self, f'{prefix}imc_var').set("")
                getattr(self, f'{prefix}imc_clasificacion_var').set("")
        except ValueError:
            getattr(self, f'{prefix}imc_var').set("")
            getattr(self, f'{prefix}imc_clasificacion_var').set("")

    def crear_examen_fisico(self, parent):
        """Crea la sección de examen físico"""
        prefix = "hist_"  # Para historia
        frame = ttk.LabelFrame(parent, text="EXAMEN FISICO", padding=15)
        frame.pack(fill=tk.X, pady=8)

        signos_frame = ttk.Frame(frame)
        signos_frame.pack(fill=tk.X, pady=(0, 10))

        row = 0
        ttk.Label(signos_frame, text="FC", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(signos_frame, text="PESO", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(signos_frame, text="ESTADO DE CONCIENCIA", font=("Arial", 10, "bold")).grid(row=row, column=2, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}fc', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        fc = getattr(self, f'{prefix}fc')
        fc.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        setattr(self, f'{prefix}peso', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        peso = getattr(self, f'{prefix}peso')
        peso.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        peso.bind('<KeyRelease>', lambda e: self.calcular_imc(prefix))

        conciencia_frame = ttk.Frame(signos_frame)
        conciencia_frame.grid(row=row, column=2, sticky="ew", padx=5, pady=5)
        ttk.Label(conciencia_frame, text="CONCIENTE", font=("Arial", 10)).pack(side=tk.LEFT)
        setattr(self, f'{prefix}conciente', ttk.Combobox(conciencia_frame, width=6, values=["SÍ", "NO"], font=("Arial", 10)))
        conciente = getattr(self, f'{prefix}conciente')
        conciente.pack(side=tk.LEFT, padx=5)

        row += 1
        ttk.Label(signos_frame, text="FR", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(signos_frame, text="TEMPERATURA", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}fr', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        fr = getattr(self, f'{prefix}fr')
        fr.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        setattr(self, f'{prefix}temperatura', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        temp = getattr(self, f'{prefix}temperatura')
        temp.grid(row=row, column=1, sticky="ew", padx=5, pady=5)

        row += 1
        ttk.Label(signos_frame, text="TA", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(signos_frame, text="TALLA", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(signos_frame, text="IMC", font=("Arial", 10, "bold")).grid(row=row, column=2, sticky="w", padx=5)

        row += 1
        setattr(self, f'{prefix}ta', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        ta = getattr(self, f'{prefix}ta')
        ta.grid(row=row, column=0, sticky="ew", padx=5, pady=5)

        setattr(self, f'{prefix}talla', ttk.Entry(signos_frame, width=12, font=("Arial", 11)))
        talla = getattr(self, f'{prefix}talla')
        talla.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        talla.bind('<KeyRelease>', lambda e: self.calcular_imc(prefix))

        imc_frame = ttk.Frame(signos_frame)
        imc_frame.grid(row=row, column=2, sticky="ew", padx=5, pady=5)

        setattr(self, f'{prefix}imc_var', tk.StringVar())
        imc_label = ttk.Label(imc_frame, textvariable=getattr(self, f'{prefix}imc_var'), font=("Arial", 11, "bold"), foreground="blue")
        imc_label.pack(side=tk.LEFT)

        setattr(self, f'{prefix}imc_clasificacion_var', tk.StringVar())
        clas_label = ttk.Label(imc_frame, textvariable=getattr(self, f'{prefix}imc_clasificacion_var'), font=("Arial", 9))
        clas_label.pack(side=tk.LEFT, padx=(10, 0))

        for i in range(3):
            signos_frame.columnconfigure(i, weight=1)

        ttk.Label(frame, text="SISTEMAS", font=("Arial", 10, "bold")).pack(anchor="w", pady=(15, 8))

        sistemas_frame = ttk.Frame(frame)
        sistemas_frame.pack(fill=tk.X, pady=(0, 10))

        # CORRECCIÓN: Sistema de 3 columnas para mejor distribución
        sistemas = [
            ("CCC:", f"{prefix}ccc_examen"),
            ("CARDIO PULMONAR:", f"{prefix}cardio_pulmonar_examen"), 
            ("ABDOMEN:", f"{prefix}abdomen_examen"),
            ("EXTREMIDADES:", f"{prefix}extremidades_examen"),
            ("GENITOURINARIO:", f"{prefix}genitourinario_examen"),
            ("NEUROLOGICO:", f"{prefix}neurologico_examen")
        ]

        self.campos_examen_fisico = {}

        for i, (label_text, attr) in enumerate(sistemas):
            row_i = i // 2  # 2 sistemas por fila
            col = (i % 2) * 2  # 0, 2, 4, etc.

            # Etiqueta del sistema
            ttk.Label(sistemas_frame, text=label_text, font=("Arial", 9, "bold")).grid(
                row=row_i, column=col, sticky="w", padx=(10, 5), pady=3)

            # Campo de entrada
            campo = ttk.Entry(sistemas_frame, width=25, font=("Arial", 9))
            campo.insert(0, "NORMAL")
            campo.grid(row=row_i, column=col+1, sticky="ew", padx=5, pady=3)

            self.campos_examen_fisico[attr] = campo

        # Configurar pesos de columnas para distribución uniforme
        sistemas_frame.columnconfigure(1, weight=1)
        sistemas_frame.columnconfigure(3, weight=1)

        ttk.Label(frame, text="DESCRIPCIÓN ADICIONAL DEL EXAMEN FÍSICO", font=("Arial", 10, "bold")).pack(anchor="w", pady=(15, 5))

        self.examen_fisico_desc = tk.Text(frame, height=4, wrap=tk.WORD, font=("Arial", 11))
        scrollbar_desc = ttk.Scrollbar(frame, orient="vertical", command=self.examen_fisico_desc.yview)
        self.examen_fisico_desc.configure(yscrollcommand=scrollbar_desc.set)

        self.examen_fisico_desc.pack(fill=tk.X, padx=5, pady=5)
        scrollbar_desc.pack(side=tk.RIGHT, fill=tk.Y)

    def crear_diagnostico(self, parent):
        """Crea la sección de diagnóstico con buscador"""
        frame = ttk.LabelFrame(parent, text="DIAGNOSTICO", padding=15)
        frame.pack(fill=tk.X, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))

        ttk.Button(btn_frame, text="🔍 Buscar Diagnóstico CIE-10", command=self.abrir_buscador_diagnosticos).pack(side=tk.LEFT)

        ttk.Label(btn_frame, text="(Haga clic para buscar en la base de datos de diagnósticos)", font=("Arial", 9, "italic")).pack(side=tk.LEFT, padx=10)

        self.diagnostico = tk.Text(frame, height=4, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.diagnostico.yview)
        self.diagnostico.configure(yscrollcommand=scrollbar.set)

        self.diagnostico.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=1, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

    def crear_conducta(self, parent):
        """Crea la sección de conducta"""
        frame = ttk.LabelFrame(parent, text="CONDUCTA", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.conducta = tk.Text(frame, height=6, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.conducta.yview)
        self.conducta.configure(yscrollcommand=scrollbar.set)

        self.conducta.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def crear_formula_medica(self, parent):
        """Crea la sección de fórmula médica"""
        frame = ttk.LabelFrame(parent, text="FORMULA MEDICA", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.formula_medica = tk.Text(frame, height=10, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.formula_medica.yview)
        self.formula_medica.configure(yscrollcommand=scrollbar.set)

        self.formula_medica.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def crear_evolucion_medica(self, parent):
        """Crea la sección de evolución médica"""
        frame = ttk.LabelFrame(parent, text="EVOLUCION MEDICA", padding=15)
        frame.pack(fill=tk.X, pady=8)

        self.evolucion_medica = tk.Text(frame, height=10, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.evolucion_medica.yview)
        self.evolucion_medica.configure(yscrollcommand=scrollbar.set)

        self.evolucion_medica.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

    def crear_datos_medico(self, parent, prefix=""):
        """Crea la sección de datos del médico con imagen de firma"""
        frame = ttk.LabelFrame(parent, text="DATOS DEL MÉDICO O PROFESIONAL DE LA SALUD", padding=15)
        frame.pack(fill=tk.X, pady=8)

        row = 0
        ttk.Label(frame, text="NOMBRE", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(frame, text="REGISTRO MÉDICO", font=("Arial", 10, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(frame, text="FIRMA Y SELLO", font=("Arial", 10, "bold")).grid(row=row, column=2, sticky="w", padx=(60, 5))

        row += 1
        setattr(self, f'{prefix}nombre_medico', ttk.Entry(frame, width=38, font=("Arial", 11)))
        nom_med = getattr(self, f'{prefix}nombre_medico')
        nom_med.insert(0, "#### #### ##### #####")
        nom_med.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        nom_med.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'nombre_medico', nom_med.get()))

        setattr(self, f'{prefix}registro_medico', ttk.Entry(frame, width=22, font=("Arial", 11)))
        reg_med = getattr(self, f'{prefix}registro_medico')
        reg_med.insert(0, "########")
        reg_med.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        reg_med.bind('<FocusOut>', lambda e: self.actualizar_shared(prefix + 'registro_medico', reg_med.get()))

        firma_frame = ttk.Frame(frame)
        firma_frame.grid(row=row, column=2, sticky="nsew", padx=5, pady=5)

        # Mostrar imagen de firma (ya cargada previamente)
        if hasattr(self, 'firma_image') and self.firma_image:
            firma_label = tk.Label(firma_frame, image=self.firma_image, bg='white')
            firma_label.pack(side=tk.TOP, pady=5)

            firma_texto_label = tk.Label(firma_frame, text="", font=("Arial", 9, "italic"), bg='white')
            firma_texto_label.pack(side=tk.TOP)
        else:
            # Fallback: campo de texto para firma
            setattr(self, f'{prefix}firma_medico', ttk.Entry(firma_frame, width=28, font=("Arial", 11)))
            firma = getattr(self, f'{prefix}firma_medico')
            firma.insert(0, "")
            firma.pack(side=tk.TOP, fill=tk.X, pady=5)

        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def crear_botones(self, parent):
        """Crea los botones de acción"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=25)

        btn_guardar = ttk.Button(frame, text="💾 GUARDAR PDF", command=self.guardar_pdf)
        btn_guardar.pack(side=tk.RIGHT, padx=(10, 0), ipadx=25, ipady=12)

        btn_limpiar = ttk.Button(frame, text="🗑️ Limpiar Formulario", command=self.limpiar_formulario)
        btn_limpiar.pack(side=tk.RIGHT, padx=10, ipadx=15, ipady=12)

        btn_ejemplo = ttk.Button(frame, text="📋 Cargar Ejemplo", command=self.cargar_ejemplo)
        btn_ejemplo.pack(side=tk.LEFT, ipadx=15, ipady=12)

    def actualizar_shared(self, key, value):
        self.datos_shared[key.replace('hist_', '').replace('form_', '').replace('evol_', '')] = value

    def actualizar_shared_from_historia(self):
        prefix = "hist_"
        self.datos_shared['fecha_dia'] = self.hist_fecha_dia.get()
        self.datos_shared['fecha_mes'] = self.hist_fecha_mes.get()
        self.datos_shared['fecha_anio'] = self.hist_fecha_anio.get()
        self.datos_shared['hora'] = self.hist_hora.get()
        self.datos_shared['nombre_paciente'] = self.hist_nombre_paciente.get()
        self.datos_shared['edad_paciente'] = self.hist_edad_paciente.get()
        self.datos_shared['sexo_paciente'] = self.hist_sexo_paciente.get()
        self.datos_shared['tipo_documento_paciente'] = self.hist_tipo_documento_paciente.get()
        self.datos_shared['documento_paciente'] = self.hist_documento_paciente.get()
        self.datos_shared['tipo_afiliado_cotiz'] = self.hist_tipo_afiliado_cotiz.get()
        self.datos_shared['ocupacion_paciente'] = self.hist_ocupacion_paciente.get()
        self.datos_shared['estado_civil'] = self.hist_estado_civil.get()
        self.datos_shared['direccion_paciente'] = self.hist_direccion_paciente.get()
        self.datos_shared['telefono_paciente'] = self.hist_telefono_paciente.get()
        self.datos_shared['nombre_medico'] = self.hist_nombre_medico.get()
        self.datos_shared['registro_medico'] = self.hist_registro_medico.get()

    def actualizar_shared_from_formula(self):
        prefix = "form_"
        self.datos_shared['fecha_dia'] = self.form_fecha_dia.get()
        self.datos_shared['fecha_mes'] = self.form_fecha_mes.get()
        self.datos_shared['fecha_anio'] = self.form_fecha_anio.get()
        self.datos_shared['hora'] = self.form_hora.get()
        self.datos_shared['nombre_paciente'] = self.form_nombre_paciente.get()
        self.datos_shared['edad_paciente'] = self.form_edad_paciente.get()
        self.datos_shared['sexo_paciente'] = self.form_sexo_paciente.get()
        self.datos_shared['tipo_documento_paciente'] = self.form_tipo_documento_paciente.get()
        self.datos_shared['documento_paciente'] = self.form_documento_paciente.get()
        self.datos_shared['tipo_afiliado_cotiz'] = self.form_tipo_afiliado_cotiz.get()
        self.datos_shared['ocupacion_paciente'] = self.form_ocupacion_paciente.get()
        self.datos_shared['estado_civil'] = self.form_estado_civil.get()
        self.datos_shared['direccion_paciente'] = self.form_direccion_paciente.get()
        self.datos_shared['telefono_paciente'] = self.form_telefono_paciente.get()
        self.datos_shared['nombre_medico'] = self.form_nombre_medico.get()
        self.datos_shared['registro_medico'] = self.form_registro_medico.get()

    def actualizar_shared_from_evolucion(self):
        prefix = "evol_"
        self.datos_shared['fecha_dia'] = self.evol_fecha_dia.get()
        self.datos_shared['fecha_mes'] = self.evol_fecha_mes.get()
        self.datos_shared['fecha_anio'] = self.evol_fecha_anio.get()
        self.datos_shared['hora'] = self.evol_hora.get()
        self.datos_shared['nombre_paciente'] = self.evol_nombre_paciente.get()
        self.datos_shared['edad_paciente'] = self.evol_edad_paciente.get()
        self.datos_shared['sexo_paciente'] = self.evol_sexo_paciente.get()
        self.datos_shared['tipo_documento_paciente'] = self.evol_tipo_documento_paciente.get()
        self.datos_shared['documento_paciente'] = self.evol_documento_paciente.get()
        self.datos_shared['tipo_afiliado_cotiz'] = self.evol_tipo_afiliado_cotiz.get()
        self.datos_shared['ocupacion_paciente'] = self.evol_ocupacion_paciente.get()
        self.datos_shared['estado_civil'] = self.evol_estado_civil.get()
        self.datos_shared['direccion_paciente'] = self.evol_direccion_paciente.get()
        self.datos_shared['telefono_paciente'] = self.evol_telefono_paciente.get()
        self.datos_shared['nombre_medico'] = self.evol_nombre_medico.get()
        self.datos_shared['registro_medico'] = self.evol_registro_medico.get()

    def actualizar_historia_from_shared(self):
        prefix = "hist_"
        self.hist_fecha_dia.delete(0, tk.END)
        self.hist_fecha_dia.insert(0, self.datos_shared.get('fecha_dia', ''))
        self.hist_fecha_mes.delete(0, tk.END)
        self.hist_fecha_mes.insert(0, self.datos_shared.get('fecha_mes', ''))
        self.hist_fecha_anio.delete(0, tk.END)
        self.hist_fecha_anio.insert(0, self.datos_shared.get('fecha_anio', ''))
        self.hist_hora.delete(0, tk.END)
        self.hist_hora.insert(0, self.datos_shared.get('hora', ''))
        self.hist_nombre_paciente.delete(0, tk.END)
        self.hist_nombre_paciente.insert(0, self.datos_shared.get('nombre_paciente', ''))
        self.hist_edad_paciente.delete(0, tk.END)
        self.hist_edad_paciente.insert(0, self.datos_shared.get('edad_paciente', ''))
        self.hist_sexo_paciente.set(self.datos_shared.get('sexo_paciente', ''))
        self.hist_tipo_documento_paciente.set(self.datos_shared.get('tipo_documento_paciente', ''))
        self.hist_documento_paciente.delete(0, tk.END)
        self.hist_documento_paciente.insert(0, self.datos_shared.get('documento_paciente', ''))
        self.hist_tipo_afiliado_cotiz.set(self.datos_shared.get('tipo_afiliado_cotiz', ''))
        self.hist_ocupacion_paciente.delete(0, tk.END)
        self.hist_ocupacion_paciente.insert(0, self.datos_shared.get('ocupacion_paciente', ''))
        self.hist_estado_civil.set(self.datos_shared.get('estado_civil', ''))
        self.hist_direccion_paciente.delete(0, tk.END)
        self.hist_direccion_paciente.insert(0, self.datos_shared.get('direccion_paciente', ''))
        self.hist_telefono_paciente.delete(0, tk.END)
        self.hist_telefono_paciente.insert(0, self.datos_shared.get('telefono_paciente', ''))
        self.hist_nombre_medico.delete(0, tk.END)
        self.hist_nombre_medico.insert(0, self.datos_shared.get('nombre_medico', '##### ###### ######## #######'))
        self.hist_registro_medico.delete(0, tk.END)
        self.hist_registro_medico.insert(0, self.datos_shared.get('registro_medico', '########'))

    def actualizar_formula_from_shared(self):
        prefix = "form_"
        self.form_fecha_dia.delete(0, tk.END)
        self.form_fecha_dia.insert(0, self.datos_shared.get('fecha_dia', ''))
        self.form_fecha_mes.delete(0, tk.END)
        self.form_fecha_mes.insert(0, self.datos_shared.get('fecha_mes', ''))
        self.form_fecha_anio.delete(0, tk.END)
        self.form_fecha_anio.insert(0, self.datos_shared.get('fecha_anio', ''))
        self.form_hora.delete(0, tk.END)
        self.form_hora.insert(0, self.datos_shared.get('hora', ''))
        self.form_nombre_paciente.delete(0, tk.END)
        self.form_nombre_paciente.insert(0, self.datos_shared.get('nombre_paciente', ''))
        self.form_edad_paciente.delete(0, tk.END)
        self.form_edad_paciente.insert(0, self.datos_shared.get('edad_paciente', ''))
        self.form_sexo_paciente.set(self.datos_shared.get('sexo_paciente', ''))
        self.form_tipo_documento_paciente.set(self.datos_shared.get('tipo_documento_paciente', ''))
        self.form_documento_paciente.delete(0, tk.END)
        self.form_documento_paciente.insert(0, self.datos_shared.get('documento_paciente', ''))
        self.form_tipo_afiliado_cotiz.set(self.datos_shared.get('tipo_afiliado_cotiz', ''))
        self.form_ocupacion_paciente.delete(0, tk.END)
        self.form_ocupacion_paciente.insert(0, self.datos_shared.get('ocupacion_paciente', ''))
        self.form_estado_civil.set(self.datos_shared.get('estado_civil', ''))
        self.form_direccion_paciente.delete(0, tk.END)
        self.form_direccion_paciente.insert(0, self.datos_shared.get('direccion_paciente', ''))
        self.form_telefono_paciente.delete(0, tk.END)
        self.form_telefono_paciente.insert(0, self.datos_shared.get('telefono_paciente', ''))
        self.form_nombre_medico.delete(0, tk.END)
        self.form_nombre_medico.insert(0, self.datos_shared.get('nombre_medico', '##### ###### ######## #######'))
        self.form_registro_medico.delete(0, tk.END)
        self.form_registro_medico.insert(0, self.datos_shared.get('registro_medico', '########'))

    def actualizar_evolucion_from_shared(self):
        prefix = "evol_"
        self.evol_fecha_dia.delete(0, tk.END)
        self.evol_fecha_dia.insert(0, self.datos_shared.get('fecha_dia', ''))
        self.evol_fecha_mes.delete(0, tk.END)
        self.evol_fecha_mes.insert(0, self.datos_shared.get('fecha_mes', ''))
        self.evol_fecha_anio.delete(0, tk.END)
        self.evol_fecha_anio.insert(0, self.datos_shared.get('fecha_anio', ''))
        self.evol_hora.delete(0, tk.END)
        self.evol_hora.insert(0, self.datos_shared.get('hora', ''))
        self.evol_nombre_paciente.delete(0, tk.END)
        self.evol_nombre_paciente.insert(0, self.datos_shared.get('nombre_paciente', ''))
        self.evol_edad_paciente.delete(0, tk.END)
        self.evol_edad_paciente.insert(0, self.datos_shared.get('edad_paciente', ''))
        self.evol_sexo_paciente.set(self.datos_shared.get('sexo_paciente', ''))
        self.evol_tipo_documento_paciente.set(self.datos_shared.get('tipo_documento_paciente', ''))
        self.evol_documento_paciente.delete(0, tk.END)
        self.evol_documento_paciente.insert(0, self.datos_shared.get('documento_paciente', ''))
        self.evol_tipo_afiliado_cotiz.set(self.datos_shared.get('tipo_afiliado_cotiz', ''))
        self.evol_ocupacion_paciente.delete(0, tk.END)
        self.evol_ocupacion_paciente.insert(0, self.datos_shared.get('ocupacion_paciente', ''))
        self.evol_estado_civil.set(self.datos_shared.get('estado_civil', ''))
        self.evol_direccion_paciente.delete(0, tk.END)
        self.evol_direccion_paciente.insert(0, self.datos_shared.get('direccion_paciente', ''))
        self.evol_telefono_paciente.delete(0, tk.END)
        self.evol_telefono_paciente.insert(0, self.datos_shared.get('telefono_paciente', ''))
        self.evol_nombre_medico.delete(0, tk.END)
        self.evol_nombre_medico.insert(0, self.datos_shared.get('nombre_medico', '##### ###### ######## #######'))
        self.evol_registro_medico.delete(0, tk.END)
        self.evol_registro_medico.insert(0, self.datos_shared.get('registro_medico', '########'))

    def abrir_buscador_diagnosticos(self):
        BuscadorDiagnosticos(self)

    def obtener_datos_formulario(self, mode):
        """Obtiene datos según el modo"""
        prefix = "hist_" if mode == "Historia Clinica" else "form_" if mode == "Formula Medica" else "evol_"
        datos = {
            'fecha': f"{getattr(self, f'{prefix}fecha_dia').get()}/{getattr(self, f'{prefix}fecha_mes').get()}/{getattr(self, f'{prefix}fecha_anio').get()}",
            'hora': getattr(self, f'{prefix}hora').get(),
            'nombre_paciente': getattr(self, f'{prefix}nombre_paciente').get(),
            'edad_paciente': getattr(self, f'{prefix}edad_paciente').get(),
            'sexo_paciente': getattr(self, f'{prefix}sexo_paciente').get(),
            'tipo_documento_paciente': getattr(self, f'{prefix}tipo_documento_paciente').get(),
            'documento_paciente': getattr(self, f'{prefix}documento_paciente').get(),
            'tipo_afiliado': getattr(self, f'{prefix}tipo_afiliado_cotiz').get(),
            'ocupacion_paciente': getattr(self, f'{prefix}ocupacion_paciente').get(),
            'estado_civil': getattr(self, f'{prefix}estado_civil').get(),
            'direccion_paciente': getattr(self, f'{prefix}direccion_paciente').get(),
            'telefono_paciente': getattr(self, f'{prefix}telefono_paciente').get(),
            'nombre_medico': getattr(self, f'{prefix}nombre_medico').get(),
            'registro_medico': getattr(self, f'{prefix}registro_medico').get(),
            'firma_medico': ""
        }
        if mode == "Historia Clinica":
            datos.update({
                'motivo_consulta': self.motivo_consulta.get("1.0", tk.END).strip(),
                'enfermedad_actual': self.enfermedad_actual.get("1.0", tk.END).strip(),
                'antecedentes': self.antecedentes.get("1.0", tk.END).strip(),
                'fc': self.hist_fc.get(),
                'peso': self.hist_peso.get(),
                'conciente': self.hist_conciente.get(),
                'fr': self.hist_fr.get(),
                'temperatura': self.hist_temperatura.get(),
                'ta': self.hist_ta.get(),
                'talla': self.hist_talla.get(),
                'imc': self.hist_imc_var.get(),
                'imc_clasificacion': self.hist_imc_clasificacion_var.get(),
                'examen_fisico_desc': self.examen_fisico_desc.get("1.0", tk.END).strip(),
                'diagnostico': self.diagnostico.get("1.0", tk.END).strip(),
                'conducta': self.conducta.get("1.0", tk.END).strip(),
            })
            # Agregar datos de los sistemas del examen físico
            for attr, campo in self.campos_examen_fisico.items():
                datos[attr] = campo.get()
        elif mode == "Formula Medica":
            datos['formula_medica'] = self.formula_medica.get("1.0", tk.END).strip()
        elif mode == "Evolucion Medica":
            datos['evolucion_medica'] = self.evolucion_medica.get("1.0", tk.END).strip()

        return datos

    def guardar_pdf(self):
        try:
            datos = self.obtener_datos_formulario(self.current_mode)

            if not datos['nombre_paciente']:
                messagebox.showerror("Error", "El nombre del paciente es obligatorio")
                return

            if not datos['documento_paciente']:
                messagebox.showerror("Error", "El documento del paciente es obligatorio")
                return

            tipo_archivo = self.current_mode.replace(" ", "_")
            nombre_archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile=f"{tipo_archivo}_{datos['nombre_paciente'].replace(' ', '_')}.pdf"
            )

            if not nombre_archivo:
                return

            if self.current_mode == "Historia Clinica":
                self.generar_pdf_historia(datos, nombre_archivo)
            elif self.current_mode == "Formula Medica":
                self.generar_pdf_formula(datos, nombre_archivo)
            elif self.current_mode == "Evolucion Medica":
                self.generar_pdf_evolucion(datos, nombre_archivo)

            messagebox.showinfo("Éxito", f"✅ {self.current_mode} guardada exitosamente\n\nArchivo: {os.path.basename(nombre_archivo)}")

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al guardar el PDF:\n{str(e)}")

    def generar_pdf_historia(self, datos, nombre_archivo):
        self.generar_pdf_completo(datos, nombre_archivo, "HISTORIA CLINICA")

    def generar_pdf_formula(self, datos, nombre_archivo):
        self.generar_pdf_completo(datos, nombre_archivo, "FORMULA MEDICA", is_simplified=True, content_key='formula_medica')

    def generar_pdf_evolucion(self, datos, nombre_archivo):
        self.generar_pdf_completo(datos, nombre_archivo, "EVOLUCION MEDICA", is_simplified=True, content_key='evolucion_medica')

    def generar_pdf_completo(self, datos, nombre_archivo, titulo, is_simplified=False, content_key=None):
        c = canvas.Canvas(nombre_archivo, pagesize=letter)
        width, height = letter

        margen_x = 40
        y = height - 40

        # Marca de agua y logo - USA resource_path
        try:
            logo_path = resource_path('Logo_Transparent.png')
            if os.path.exists(logo_path):
                c.saveState()
                c.setFillAlpha(0.28)
                x_center = (width - 750) / 2
                y_center = (height - 650) / 2
                c.drawImage(logo_path, x_center, y_center, width=700, height=950, preserveAspectRatio=True, mask='auto')
                c.restoreState()
        except Exception as e:
            print(f"Error cargando logo transparente: {e}")

        try:
            logo_path = resource_path('FullLogo_Transparent.png')
            if os.path.exists(logo_path):
                logo_y = y - 90 + 30  # Ajuste
                c.drawImage(logo_path, margen_x, logo_y, width=120, height=90, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error cargando logo completo: {e}")

        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, y - 10, titulo)
        y -= 28

        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, y, "MEDICO INTERNISTA UNIVERSIDAD DE ZULIA")
        y -= 25

        c.line(margen_x, y, width - margen_x, y)
        y -= 15

        # Encabezado
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margen_x, y, "FECHA")
        c.drawString(margen_x + 120, y, "HORA")
        y -= 12

        c.setFont("Helvetica", 9)
        c.drawString(margen_x, y, datos['fecha'])
        c.drawString(margen_x + 120, y, datos['hora'])
        y -= 20

        # Datos del paciente (mismo para todos)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margen_x, y, "DATOS DEL PACIENTE")
        y -= 15

        c.setFont("Helvetica-Bold", 8)
        c.drawString(margen_x, y, "NOMBRE")
        c.drawString(margen_x + 300, y, "EDAD")
        c.drawString(margen_x + 380, y, "SEXO")
        y -= 12

        c.setFont("Helvetica", 8)
        c.drawString(margen_x, y, datos['nombre_paciente'])
        c.drawString(margen_x + 300, y, datos['edad_paciente'])
        c.drawString(margen_x + 380, y, datos['sexo_paciente'])
        y -= 15

        c.setFont("Helvetica-Bold", 8)
        c.drawString(margen_x, y, "TIPO DOCUMENTO")
        c.drawString(margen_x + 100, y, "No. DOCUMENTO IDENTIDAD")
        c.drawString(margen_x + 280, y, "TIPO AFILIADO")
        c.drawString(margen_x + 380, y, "OCUPACIÓN")
        y -= 12

        c.setFont("Helvetica", 8)
        c.drawString(margen_x, y, datos['tipo_documento_paciente'])
        c.drawString(margen_x + 100, y, datos['documento_paciente'])
        c.drawString(margen_x + 280, y, datos['tipo_afiliado'])
        c.drawString(margen_x + 380, y, datos['ocupacion_paciente'])
        y -= 15

        c.setFont("Helvetica-Bold", 8)
        c.drawString(margen_x, y, "ESTADO CIVIL")
        c.drawString(margen_x + 100, y, "DIRECCIÓN RESIDENCIA")
        c.drawString(margen_x + 380, y, "TELÉFONO")
        y -= 12

        c.setFont("Helvetica", 8)
        c.drawString(margen_x, y, datos['estado_civil'])
        c.drawString(margen_x + 100, y, datos['direccion_paciente'][:40])
        c.drawString(margen_x + 380, y, datos['telefono_paciente'])
        y -= 20

        if is_simplified:
            # Contenido simplificado
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, titulo.upper())
            y -= 12

            c.setFont("Helvetica", 8)
            texto = datos[content_key]
            lineas = simpleSplit(texto, "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10
        else:
            # Contenido completo de historia (como original)
            # MOTIVO DE CONSULTA
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "MOTIVO DE CONSULTA")
            y -= 12

            c.setFont("Helvetica", 8)
            lineas = simpleSplit(datos['motivo_consulta'], "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas[:3]:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10

            # ENFERMEDAD ACTUAL
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "ENFERMEDAD ACTUAL")
            y -= 12

            c.setFont("Helvetica", 8)
            lineas = simpleSplit(datos['enfermedad_actual'], "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas[:4]:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10

            # ANTECEDENTES
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "ANTECEDENTES")
            y -= 12

            c.setFont("Helvetica", 8)
            lineas = simpleSplit(datos['antecedentes'], "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas[:4]:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10

            # EXAMEN FÍSICO
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "EXAMEN FISICO")
            y -= 15

            c.setFont("Helvetica-Bold", 8)
            c.drawString(margen_x, y, "FC")
            c.drawString(margen_x + 80, y, "PESO")
            c.drawString(margen_x + 160, y, "ESTADO DE CONCIENCIA")
            y -= 12

            c.setFont("Helvetica", 8)
            c.drawString(margen_x, y, datos['fc'])
            c.drawString(margen_x + 80, y, datos['peso'])
            c.drawString(margen_x + 160, y, f"CONCIENTE: {datos['conciente']}")
            y -= 15

            c.setFont("Helvetica-Bold", 8)
            c.drawString(margen_x, y, "FR")
            c.drawString(margen_x + 80, y, "TEMPERATURA")
            y -= 12

            c.setFont("Helvetica", 8)
            c.drawString(margen_x, y, datos['fr'])
            c.drawString(margen_x + 80, y, datos['temperatura'])
            y -= 15

            c.setFont("Helvetica-Bold", 8)
            c.drawString(margen_x, y, "TA")
            c.drawString(margen_x + 80, y, "TALLA")
            c.drawString(margen_x + 160, y, "IMC")
            y -= 12

            c.setFont("Helvetica", 8)
            c.drawString(margen_x, y, datos['ta'])
            c.drawString(margen_x + 80, y, datos['talla'])
            c.drawString(margen_x + 160, y, f"{datos.get('imc', '')} ({datos.get('imc_clasificacion', '')})")
            y -= 15

            # CORRECCIÓN: SISTEMAS ORGANIZADOS EN PDF
            c.setFont("Helvetica-Bold", 8)
            c.drawString(margen_x, y, "SISTEMAS")
            y -= 12

            c.setFont("Helvetica", 8)
            
            # Definir sistemas con sus valores
            sistemas_pdf = [
                ("CCC:", datos.get('hist_ccc_examen', 'NORMAL')),
                ("CARDIO PULMONAR:", datos.get('hist_cardio_pulmonar_examen', 'NORMAL')),
                ("ABDOMEN:", datos.get('hist_abdomen_examen', 'NORMAL')),
                ("EXTREMIDADES:", datos.get('hist_extremidades_examen', 'NORMAL')),
                ("GENITOURINARIO:", datos.get('hist_genitourinario_examen', 'NORMAL')),
                ("NEUROLOGICO:", datos.get('hist_neurologico_examen', 'NORMAL'))
            ]

            # Mostrar sistemas en 2 columnas
            col1_x = margen_x
            col2_x = width / 2
            
            for i, (nombre, valor) in enumerate(sistemas_pdf):
                if i % 2 == 0:  # Columna izquierda
                    x_pos = col1_x
                    current_y = y
                else:  # Columna derecha
                    x_pos = col2_x
                    current_y = y - (12 * (i // 6))
                
                texto_sistema = f"{nombre} {valor}" if valor else f"{nombre} NORMAL"
                c.drawString(x_pos, current_y, texto_sistema)
                
                # Solo incrementar Y después de completar un par
                if i % 2 == 1:
                    y -= 12

            # Ajustar posición Y después de mostrar todos los sistemas
            if len(sistemas_pdf) % 2 == 1:  # Si hay número impar de sistemas
                y -= 12
            y -= 10

            if datos.get('examen_fisico_desc'):
                c.setFont("Helvetica-Bold", 8)
                c.drawString(margen_x, y, "DESCRIPCIÓN ADICIONAL")
                y -= 12

                c.setFont("Helvetica", 8)
                lineas = simpleSplit(datos['examen_fisico_desc'], "Helvetica", 8, width - 2 * margen_x)
                for linea in lineas[:3]:
                    c.drawString(margen_x, y, linea)
                    y -= 10
                y -= 10

            # DIAGNÓSTICO
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "DIAGNOSTICO")
            y -= 12

            c.setFont("Helvetica", 8)
            lineas = simpleSplit(datos['diagnostico'], "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas[:3]:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10

            # CONDUCTA
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "CONDUCTA")
            y -= 12

            c.setFont("Helvetica", 8)
            lineas = simpleSplit(datos['conducta'], "Helvetica", 8, width - 2 * margen_x)
            for linea in lineas[:5]:
                c.drawString(margen_x, y, linea)
                y -= 10
            y -= 10

        # Datos del médico
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margen_x, y, "DATOS DEL MÉDICO O PROFESIONAL DE LA SALUD")
        y -= 15

        c.setFont("Helvetica-Bold", 8)
        c.drawString(margen_x, y, "NOMBRE")
        c.drawString(margen_x + 250, y, "REGISTRO MÉDICO")
        c.drawString(margen_x + 400, y, "FIRMA Y SELLO")
        y -= 12

        c.setFont("Helvetica", 8)
        c.drawString(margen_x, y, datos['nombre_medico'])
        c.drawString(margen_x + 250, y, datos['registro_medico'])
        c.drawString(margen_x + 400, y, datos['firma_medico'])

        # Para la firma al final del PDF - USA resource_path
        try:
            firma_path = resource_path('firma.png')
            if os.path.exists(firma_path):
                firma_y = y - 50  # Más espacio arriba para firma más grande
                 # Firma más grande
                c.drawImage(firma_path, margen_x + 380, firma_y, width=120, height=85, preserveAspectRatio=True, mask='auto')        
        except Exception as e:
            print(f"Error cargando firma en PDF: {e}")

        c.save()

    def limpiar_formulario(self):
        respuesta = messagebox.askyesno("Limpiar Formulario", "¿Está seguro de que desea limpiar todos los campos del formulario?")
        if not respuesta:
            return

        # Limpiar datos shared
        self.datos_shared = {}

        # Limpiar según modo actual
        if self.current_mode == "Historia Clinica":
            self.limpiar_historia()
        elif self.current_mode == "Formula Medica":
            self.limpiar_formula()
        elif self.current_mode == "Evolucion Medica":
            self.limpiar_evolucion()

        messagebox.showinfo("Formulario Limpio", "Todos los campos han sido limpiados correctamente.")

    def limpiar_historia(self):
        ahora = datetime.now()
        self.hist_fecha_dia.delete(0, tk.END)
        self.hist_fecha_dia.insert(0, ahora.strftime("%d"))
        self.hist_fecha_mes.delete(0, tk.END)
        self.hist_fecha_mes.insert(0, ahora.strftime("%m"))
        self.hist_fecha_anio.delete(0, tk.END)
        self.hist_fecha_anio.insert(0, ahora.strftime("%Y"))
        self.hist_hora.delete(0, tk.END)
        self.hist_hora.insert(0, ahora.strftime("%H:%M"))

        self.hist_nombre_paciente.delete(0, tk.END)
        self.hist_edad_paciente.delete(0, tk.END)
        self.hist_documento_paciente.delete(0, tk.END)
        self.hist_ocupacion_paciente.delete(0, tk.END)
        self.hist_direccion_paciente.delete(0, tk.END)
        self.hist_telefono_paciente.delete(0, tk.END)
        self.hist_fc.delete(0, tk.END)
        self.hist_peso.delete(0, tk.END)
        self.hist_fr.delete(0, tk.END)
        self.hist_temperatura.delete(0, tk.END)
        self.hist_ta.delete(0, tk.END)
        self.hist_talla.delete(0, tk.END)
        self.hist_nombre_medico.delete(0, tk.END)
        self.hist_nombre_medico.insert(0, "##### ###### ######## ####### ")
        self.hist_registro_medico.delete(0, tk.END)
        self.hist_registro_medico.insert(0, "########")

        self.hist_sexo_paciente.set('')
        self.hist_tipo_documento_paciente.set('')
        self.hist_tipo_afiliado_cotiz.set('')
        self.hist_estado_civil.set('')
        self.hist_conciente.set('')

        for campo in self.campos_examen_fisico.values():
            campo.delete(0, tk.END)
            campo.insert(0, "NORMAL")

        self.hist_imc_var.set("")
        self.hist_imc_clasificacion_var.set("")

        self.motivo_consulta.delete("1.0", tk.END)
        self.enfermedad_actual.delete("1.0", tk.END)
        self.antecedentes.delete("1.0", tk.END)
        self.diagnostico.delete("1.0", tk.END)
        self.conducta.delete("1.0", tk.END)
        self.examen_fisico_desc.delete("1.0", tk.END)

    def limpiar_formula(self):
        ahora = datetime.now()
        self.form_fecha_dia.delete(0, tk.END)
        self.form_fecha_dia.insert(0, ahora.strftime("%d"))
        self.form_fecha_mes.delete(0, tk.END)
        self.form_fecha_mes.insert(0, ahora.strftime("%m"))
        self.form_fecha_anio.delete(0, tk.END)
        self.form_fecha_anio.insert(0, ahora.strftime("%Y"))
        self.form_hora.delete(0, tk.END)
        self.form_hora.insert(0, ahora.strftime("%H:%M"))

        self.form_nombre_paciente.delete(0, tk.END)
        self.form_edad_paciente.delete(0, tk.END)
        self.form_documento_paciente.delete(0, tk.END)
        self.form_ocupacion_paciente.delete(0, tk.END)
        self.form_direccion_paciente.delete(0, tk.END)
        self.form_telefono_paciente.delete(0, tk.END)
        self.form_nombre_medico.delete(0, tk.END)
        self.form_nombre_medico.insert(0, "##### ###### ######## ####### ")
        self.form_registro_medico.delete(0, tk.END)
        self.form_registro_medico.insert(0, "########")

        self.form_sexo_paciente.set('')
        self.form_tipo_documento_paciente.set('')
        self.form_tipo_afiliado_cotiz.set('')
        self.form_estado_civil.set('')

        self.formula_medica.delete("1.0", tk.END)

    def limpiar_evolucion(self):
        ahora = datetime.now()
        self.evol_fecha_dia.delete(0, tk.END)
        self.evol_fecha_dia.insert(0, ahora.strftime("%d"))
        self.evol_fecha_mes.delete(0, tk.END)
        self.evol_fecha_mes.insert(0, ahora.strftime("%m"))
        self.evol_fecha_anio.delete(0, tk.END)
        self.evol_fecha_anio.insert(0, ahora.strftime("%Y"))
        self.evol_hora.delete(0, tk.END)
        self.evol_hora.insert(0, ahora.strftime("%H:%M"))

        self.evol_nombre_paciente.delete(0, tk.END)
        self.evol_edad_paciente.delete(0, tk.END)
        self.evol_documento_paciente.delete(0, tk.END)
        self.evol_ocupacion_paciente.delete(0, tk.END)
        self.evol_direccion_paciente.delete(0, tk.END)
        self.evol_telefono_paciente.delete(0, tk.END)
        self.evol_nombre_medico.delete(0, tk.END)
        self.evol_nombre_medico.insert(0, "##### ###### ######## ####### ")
        self.evol_registro_medico.delete(0, tk.END)
        self.evol_registro_medico.insert(0, "########")

        self.evol_sexo_paciente.set('')
        self.evol_tipo_documento_paciente.set('')
        self.evol_tipo_afiliado_cotiz.set('')
        self.evol_estado_civil.set('')

        self.evolucion_medica.delete("1.0", tk.END)

    def cargar_ejemplo(self):
        ahora = datetime.now()
        ejemplo = {
            'fecha_dia': ahora.strftime("%d"),
            'fecha_mes': ahora.strftime("%m"),
            'fecha_anio': ahora.strftime("%Y"),
            'hora': ahora.strftime("%H:%M"),
            'nombre_paciente': "ANA MARÍA GARCÍA LÓPEZ",
            'edad_paciente': "42",
            'sexo_paciente': "F",
            'tipo_documento_paciente': "C.C.",
            'documento_paciente': "45567543",
            'tipo_afiliado_cotiz': "BENEF",
            'ocupacion_paciente': "ENFERMERA",
            'estado_civil': "CASADO",
            'direccion_paciente': "Carrera 56 #23-45, Bogotá D.C.",
            'telefono_paciente': "3157894561",
            'motivo_consulta': "Control médico rutinario y evaluación de dolor abdominal intermitente.",
            'enfermedad_actual': "Paciente refiere dolor abdominal en hipogastrio de 2 semanas de evolución, intermitente, de intensidad moderada.",
            'antecedentes': "HTA diagnosticada hace 5 años, controlada con Losartán 50mg. Niega alergias medicamentosas.",
            'fc': "78",
            'peso': "65",
            'conciente': "SÍ",
            'fr': "16",
            'temperatura': "36.8",
            'ta': "120/80",
            'talla': "165",
            'examen_fisico_desc': "Paciente en buen estado general. Abdomen blando, depresible, doloroso a la palpación en hipogastrio. Resto del examen físico sin hallazgos relevantes.",
            'diagnostico': "R104 - OTROS DOLORES ABDOMINALES Y LOS NO ESPECIFICADOS",
            'conducta': "1. Solicitar ecografía abdominal\n2. Control de presión arterial en 15 días\n3. Paracetamol 500mg cada 8 horas por 3 días si dolor\n4. Recomendaciones dietéticas",
            'formula_medica': "Ejemplo de fórmula: Paracetamol 500mg cada 8 horas",
            'evolucion_medica': "Ejemplo de evolución: Paciente mejora con tratamiento",
            'nombre_medico': "##### ###### ######## ####### ",
            'registro_medico': "########"
        }

        self.datos_shared.update(ejemplo)

        if self.current_mode == "Historia Clinica":
            self.actualizar_historia_from_shared()
            self.motivo_consulta.insert("1.0", ejemplo['motivo_consulta'])
            self.enfermedad_actual.insert("1.0", ejemplo['enfermedad_actual'])
            self.antecedentes.insert("1.0", ejemplo['antecedentes'])
            self.hist_fc.insert(0, ejemplo['fc'])
            self.hist_peso.insert(0, ejemplo['peso'])
            self.hist_conciente.set(ejemplo['conciente'])
            self.hist_fr.insert(0, ejemplo['fr'])
            self.hist_temperatura.insert(0, ejemplo['temperatura'])
            self.hist_ta.insert(0, ejemplo['ta'])
            self.hist_talla.insert(0, ejemplo['talla'])
            self.calcular_imc("hist_")
            self.examen_fisico_desc.insert("1.0", ejemplo['examen_fisico_desc'])
            self.diagnostico.insert("1.0", ejemplo['diagnostico'])
            self.conducta.insert("1.0", ejemplo['conducta'])
        elif self.current_mode == "Formula Medica":
            self.actualizar_formula_from_shared()
            self.formula_medica.insert("1.0", ejemplo['formula_medica'])
        elif self.current_mode == "Evolucion Medica":
            self.actualizar_evolucion_from_shared()
            self.evolucion_medica.insert("1.0", ejemplo['evolucion_medica'])

        messagebox.showinfo("Ejemplo Cargado", "Datos de ejemplo cargados correctamente.")

def main():
    try:
        root = tk.Tk()
        app = GeneradorHistoriaClinica(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"No se pudo iniciar la aplicación: {str(e)}")

if __name__ == "__main__":
    main()