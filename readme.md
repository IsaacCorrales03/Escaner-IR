# Sistema de Gestión de Becas de Comedor

Este proyecto implementa un sistema completo para gestionar cédulas estudiantiles mediante una base de datos SQLite. El sistema permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) sobre registros de cédulas estudiantiles, utilizando un escáner OCR para la detección automática de cédulas a través de la cámara web. El objetivo principal es facilitar la gestión de becas de comedor mediante un sistema de verificación eficiente.

## Estructura del Proyecto

El proyecto se compone de 4 archivos principales y una carpeta de recursos:

- **UI.py**: Interfaz gráfica desarrollada con la biblioteca Flet
- **db.py**: Script para la creación y estructura de la base de datos
- **IR_scanner.py**: Implementación del escáner OCR para procesar identificaciones
- **GestorPrincipal.py**: Implementación de operaciones CRUD sobre la base de datos
- **assets/**: Carpeta con imágenes y sonidos utilizados por la aplicación

## Componentes del Sistema

### 1. Base de Datos (db.py)

Este módulo se encarga de crear y configurar la base de datos SQLite que almacenará la información de los estudiantes.

```python
def crear_base_de_datos(nombre_db="cedulas.db"):
    """
    Crea la base de datos SQLite y la tabla para el sistema de registro de cédulas.
    """
    try:
        # Verificar si el archivo ya existe
        if os.path.exists(nombre_db):
            print(f"La base de datos '{nombre_db}' ya existe.")
        else:
            print(f"Creando nueva base de datos '{nombre_db}'")
            
        # Conectar a la base de datos (la crea si no existe)
        conexion = sqlite3.connect(nombre_db)
        cursor = conexion.cursor()
        
        # Crear la tabla cedulas_registradas
        crear_tabla_query = """
        CREATE TABLE IF NOT EXISTS cedulas_registradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_estudiante TEXT NOT NULL,
            numero_de_cedula TEXT NOT NULL UNIQUE,
            codigo_hash TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            año TEXT NOT NULL,
            sección TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(crear_tabla_query)
        print("Tabla 'cedulas_registradas' creada o ya existente")
        
        # Crear índices para optimizar búsquedas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cedula ON cedulas_registradas(numero_de_cedula)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON cedulas_registradas(codigo_hash)")
        
        # Confirmar cambios
        conexion.commit()
        
    except sqlite3.Error as e:
        print(f"Error SQLite: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()
```

**Características técnicas**:
- Crea una tabla `cedulas_registradas` con estructura específica para información estudiantil:
  - `id`: Identificador único autoincremental
  - `nombre_estudiante`: Nombre completo del estudiante
  - `numero_de_cedula`: Número de cédula único (con restricción UNIQUE)
  - `codigo_hash`: Hash SHA-256 generado para la cédula
  - `especialidad`: Campo para la especialidad académica
  - `año`: Año académico del estudiante
  - `sección`: Sección o grupo del estudiante
  - `fecha_registro`: Timestamp automático de la creación del registro
- Implementa índices para optimizar las búsquedas por cédula (`idx_cedula`) y hash (`idx_hash`)
- Verifica la existencia previa de la base de datos para evitar recreación
- Utiliza manejo de excepciones específicas para errores de SQLite
- Garantiza el cierre de conexiones mediante bloque `finally`

### 2. Gestor Principal (GestorPrincipal.py)

Este módulo implementa el patrón Singleton para gestionar las operaciones CRUD sobre la base de datos, garantizando una única instancia de conexión en toda la aplicación.

**Características técnicas**:
- **Patrón Singleton**: Implementado con un lock thread-safe para entornos multithread
  ```python
  def __new__(cls, db_file="cedulas.db"):
      with cls._lock:
          if cls._instance is None:
              cls._instance = super(GestorCedulas, cls).__new__(cls)
              cls._instance._initialized = False
      return cls._instance
  ```

- **Conexión a la base de datos**: Configurada para devolver filas como diccionarios
  ```python
  self.conexion = sqlite3.connect(db_file, check_same_thread=False)
  self.conexion.row_factory = sqlite3.Row
  ```

- **Generación de hash**: Implementa SHA-256 para crear identificadores únicos para cada cédula
  ```python
  def generar_hash(self, numero_cedula):
      hash_object = hashlib.sha256(str(numero_cedula).encode())
      return hash_object.hexdigest()
  ```

- **Operaciones CRUD**:
  - `crear_registro()`: Inserta nuevos estudiantes con validación de datos
  - `buscar_por_cedula()`: Localiza estudiantes mediante su número de cédula
  - `listar_registros()`: Recupera todos los registros como lista de diccionarios
  - `actualizar_registro()`: Permite modificar campos específicos con validación
  - `eliminar_registro()`: Elimina registros por número de cédula con confirmación

- **Seguridad y validación**:
  - Filtrado de campos permitidos para actualización
  - Conversión de resultados a diccionarios para mejor manejo
  - Manejo de transacciones con `commit()`

### 3. Escáner de Cédula (IR_scanner.py)

Este módulo implementa la detección de cédulas mediante procesamiento de imágenes y OCR (Reconocimiento Óptico de Caracteres).

**Características técnicas**:
- **Procesamiento en tiempo real**: Captura y analiza frames de video continuamente
  ```python
  def _loop_escaneo(self):
      if not self.inicializar():
          return
      
      while self.running:
          ret, self.frame = self.cap.read()
          # Procesamiento y análisis...
  ```

- **EasyOCR con configuración específica**: 
  ```python
  self.reader = easyocr.Reader(['es'])  # Modelo optimizado para español
  ```

- **Detección de cédulas**: Algoritmo específico para validar números de cédula
  ```python
  # Verificar si es un número de cédula válido (9 dígitos y buena confianza)
  if conf >= 0.60 and len(texto_limpio) == 9 and texto_limpio.isdigit():
      # Procesamiento de cédula encontrada...
  ```

- **Visualización de detección**: Dibuja contornos en tiempo real
  ```python
  # Dibujar bounding box
  (tl, tr, br, bl) = bbox
  puntos = [tuple(map(int, tl)), tuple(map(int, tr)), tuple(map(int, br)), tuple(map(int, bl))]
  cv2.polylines(self.frame, [np.array(puntos)], isClosed=True, color=(0, 255, 0), thickness=2)
  ```

- **Sistema de callbacks**: Implementa tres callbacks para comunicación con la UI
  - `on_cedula_found`: Notifica cuando se encuentra una cédula válida
  - `on_scan_failed`: Informa cuando falla la detección
  - `on_frame_update`: Actualiza la UI con cada frame procesado

- **Conversión de imagen eficiente**: Procesa frames para transmisión a la UI
  ```python
  # Convertir el frame de OpenCV a formato adecuado para Flet
  rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
  pil_img = Image.fromarray(rgb_frame)
  ```

### 4. Interfaz de Usuario (UI.py)

Implementa una interfaz gráfica moderna y responsiva utilizando la biblioteca Flet (basada en Flutter para Python).

**Componentes principales**:

1. **Clase `CedulaApp`**: Clase principal que maneja toda la aplicación
   ```python
   class CedulaApp:
       def __init__(self):
           self.escaner = None
           self.cedula_encontrada = None
           # Inicialización de componentes...
   ```

2. **Sistema de pestañas**: Organiza la funcionalidad en 4 pestañas principales
   ```python
   tabs = ft.Tabs(
       selected_index=0,
       animation_duration=300,
       tabs=[tab_escaneo, tab_crear, tab_buscar, tab_listar],
       expand=True,
   )
   ```

3. **Visor de cámara en vivo**:
   ```python
   self.img_view = ft.Image(
       src="assets/desactivar-camara.png",
       width=640,
       height=480,
       fit=ft.ImageFit.CONTAIN,
       border_radius=10,
   )
   ```

4. **Formularios interactivos**: 
   ```python
   # Campos para el formulario
   self.nombre_input = ft.TextField(label="Nombre del Estudiante", width=400)
   self.cedula_input = ft.TextField(label="Número de Cédula", width=400)
   # Más campos...
   ```

5. **Tabla de datos**:
   ```python
   self.tabla_registros = ft.DataTable(
       columns=[
           ft.DataColumn(ft.Text("Nombre")),
           ft.DataColumn(ft.Text("Cédula")),
           # Más columnas...
       ],
       rows=[],
       border=ft.border.all(1, ft.Colors.GREY_400),
       # Configuración adicional...
   )
   ```

6. **Diálogos modales**: Para mostrar resultados de escaneo y confirmaciones
   ```python
   modal_dlg = ft.AlertDialog(
       modal=True,
       title=ft.Text("Estudiante Registrado", size=24, weight=ft.FontWeight.BOLD),
       content=ft.Column([
           # Contenido del diálogo...
       ]),
       actions=[
           ft.TextButton("Continuar Escaneando", on_click=lambda e: self.page.close(modal_dlg)),
       ],
   )
   ```

7. **Retroalimentación sonora**:
   ```python
   # Inicialización de pygame para sonido
   pygame.init()
   pygame.mixer.init()
   
   # Reproducción de sonidos
   sonido = pygame.mixer.Sound('assets/success.mp3')
   sonido.play()
   ```

**Flujo de trabajo principal**:

1. **Escaneo de cédula**:
   - Inicialización de la cámara y el motor OCR
   - Procesamiento continuo de frames en busca de cédulas
   - Notificación visual y sonora al detectar cédulas
   - Verificación automática en la base de datos

2. **Gestión de registros**:
   - Creación de nuevos registros con validación
   - Búsqueda de registros por número de cédula
   - Actualización de información existente
   - Eliminación de registros con confirmación
   - Visualización tabular de todos los registros

## Tecnologías Utilizadas

### 1. Procesamiento de Imágenes y OCR
- **OpenCV (cv2)**: Biblioteca para procesamiento de imágenes y video en tiempo real
  - Utilizado para captura de video, dibujo de contornos y preprocesamiento
  - Versión recomendada: 4.5.0 o superior

- **EasyOCR**: Motor OCR de código abierto para reconocimiento de texto en imágenes
  - Configurado con modelo español para mejor reconocimiento de cédulas
  - Incluye análisis de confianza en cada detección

- **NumPy**: Biblioteca para cálculos numéricos y manipulación de matrices
  - Utilizada para transformaciones de coordenadas y manipulación de imágenes

- **PIL (Pillow)**: Biblioteca para procesamiento de imágenes
  - Usada para conversión entre formatos de imagen

### 2. Interfaz de Usuario
- **Flet**: Framework para crear interfaces gráficas multiplataforma con Flutter y Python
  - Componentes responsive usados: Tabs, DataTable, TextField, Container, Column, Row
  - Soporte para imágenes, botones y diálogos

- **Pygame**: Biblioteca para manejo de sonidos y multimedia
  - Utilizada para reproducir efectos sonoros de éxito/fracaso

### 3. Base de Datos
- **SQLite3**: Motor de base de datos relacional ligero
  - Configurado con índices para optimizar consultas frecuentes
  - Utiliza Row Factory para trabajar con resultados como diccionarios

- **Hashlib**: Biblioteca para generar hashes criptográficos
  - Implementa SHA-256 para generar identificadores únicos

### 4. Paralelismo
- **Threading**: Módulo para implementar concurrencia mediante hilos
  - Permite la captura de video sin bloquear la interfaz
  - Implementa cooldown para evitar múltiples detecciones

- **Lock**: Mecanismo para garantizar la exclusión mutua en el patrón Singleton
  - Previene condiciones de carrera en la creación de instancias

## Instrucciones de Uso

### Requisitos Previos
1. Python 3.7 o superior
2. Instalar las dependencias:
   ```
   pip install flet opencv-python easyocr numpy pillow pygame
   ```

### Configuración Inicial
1. Asegúrese de tener una cámara web conectada y funcional
2. Cree una carpeta `assets` en el directorio del proyecto con:
   - `success.mp3`: Sonido para cédula encontrada en el sistema
   - `wrong.mp3`: Sonido para cédula no registrada
   - `desactivar-camara.png`: Imagen para mostrar cuando la cámara está inactiva

### Ejecución del Sistema
1. Asegúrese de que todos los archivos del proyecto estén en el mismo directorio
2. Ejecute el archivo principal:
   ```
   python UI.py
   ```
3. La aplicación se iniciará mostrando la interfaz de usuario con las pestañas

### Funcionalidades en Detalle

#### Escaneo de Cédulas
1. Vaya a la pestaña "Escaneo"
2. Haga clic en "Iniciar Escaneo"
   - La cámara se activará y mostrará video en vivo
   - El sistema analizará automáticamente cada frame
3. Coloque la cédula frente a la cámara
   - Mantenga buena iluminación para mejorar la detección
   - El número debe ser claramente visible y enfocado
4. Cuando se detecte un número válido:
   - Se mostrará un recuadro verde alrededor del número
   - El sistema verificará en la base de datos
   - Se reproducirá un sonido indicando éxito o fracaso
   - Aparecerá un diálogo con la información del estudiante o aviso de no registro
5. Para detener el escaneo, haga clic en "Detener Escaneo"

#### Registro de Estudiantes
1. Vaya a la pestaña "Crear Registro"
2. Complete todos los campos del formulario:
   - **Nombre del Estudiante**: Nombre completo 
   - **Número de Cédula**: Identificación única (9 dígitos)
   - **Especialidad**: Área de estudio
   - **Año**: Año académico
   - **Sección**: Grupo o sección
3. Haga clic en "Crear Registro"
   - El sistema validará los datos ingresados
   - Generará un hash único para la cédula
   - Almacenará la información en la base de datos
   - Mostrará un mensaje de confirmación

#### Búsqueda y Administración
1. Vaya a la pestaña "Buscar y Administrar"
2. Ingrese el número de cédula a buscar
3. Haga clic en "Buscar"
4. Si el registro existe:
   - Se mostrarán todos los datos del estudiante
   - Podrá modificar la información en los campos del formulario
   - Haga clic en "Actualizar con Datos del Formulario" para guardar cambios
   - Haga clic en "Eliminar Registro" para eliminar el estudiante
5. Si el registro no existe:
   - Se mostrará un mensaje indicando que no se encontró

#### Visualización de Registros
1. Vaya a la pestaña "Ver Todos los Registros"
2. Se mostrará una tabla con todos los estudiantes registrados:
   - Nombre
   - Número de cédula
   - Especialidad
   - Año
   - Sección
3. Haga clic en "Refrescar Listado" para actualizar la tabla con los datos más recientes

## Consideraciones Adicionales

- **Rendimiento del OCR**: 
  - El sistema está configurado para detectar números de 9 dígitos con un nivel de confianza mínimo de 0.60
  - Mejores resultados se obtienen con buena iluminación y cédulas limpias

- **Seguridad**:
  - Las cédulas se almacenan con un hash SHA-256 para verificación
  - La base de datos implementa restricciones UNIQUE para evitar duplicados

- **Thread Safety**:
  - El sistema maneja correctamente múltiples hilos para la UI y el procesamiento OCR
  - Implementa locks para prevenir condiciones de carrera

- **Manejo de recursos**:
  - La cámara se libera adecuadamente al detener el escaneo
  - Las conexiones a la base de datos se cierran correctamente

- **Extensibilidad**:
  - El diseño modular facilita la incorporación de nuevas funcionalidades
  - El patrón Singleton permite acceder al gestor desde cualquier parte de la aplicación

---

## Diagrama de Flujo del Sistema

```
┌──────────────────────────────────────────┐
│                                          │
│                  UI.py                   │
│                                          │
├──────────┬───────────────┬───────────────┤
│          │               │               │
│ Escaneo  │   Creación    │  Búsqueda y   │
│          │               │ Administración│
└────┬─────┴───────┬───────┴───────┬───────┘
     │             │               │
     ▼             │               │
┌────────────┐     │               │
│            │     │               │
│IR_scanner.py│     │               │
│            │     │               │
└─────┬──────┘     │               │
      │            │               │
      │            ▼               ▼
      │      ┌─────────────────────────────┐
      └─────►│                             │
             │     GestorPrincipal.py      │
             │                             │
             └──────────────┬──────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │               │
                    │    db.py      │
                    │               │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │               │
                    │  cedulas.db   │
                    │               │
                    └───────────────┘
```

## Posibles Mejoras Futuras

1. **Integración con API externa**: Para verificar la validez de las cédulas
2. **Exportación de datos**: Funcionalidad para exportar registros a Excel o PDF
3. **Sistema de usuarios**: Implementar autenticación para diferentes niveles de acceso
4. **Estadísticas y reportes**: Análisis estadístico de estudiantes registrados
5. **Mejoras en el OCR**: Implementar algoritmos de preprocesamiento para mejorar detección
6. **Respaldo automático**: Sistema de respaldo periódico de la base de datos