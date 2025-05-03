import flet as ft
from GestorPrincipal import GestorCedulas
from IR_scanner import EscanerCedula
import base64
import pygame

pygame.init()
pygame.mixer.init()

gestor = GestorCedulas()

class CedulaApp:
    def __init__(self):
        self.escaner = None
        self.cedula_encontrada = None
        self.img_view = None
        self.status_text = None
        self.cedula_text = None
        self.main_page = None
        self.cedula_dialog = None
        self.page = None
        self.detenido = False

        # Campos para el formulario
        self.nombre_input = None
        self.cedula_input = None
        self.especialidad_input = None
        self.anio_input = None
        self.seccion_input = None
        self.buscar_cedula_input = None
        self.resultado_container = None
        self.tabla_registros = None
        self.mensaje_estado = None
        self.escaner = None

    def iniciar_app(self, page: ft.Page):
        self.page = page
        page.title = "Escáner de Cédula"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.window_width = 800
        page.window_height = 600
        
        # Crear componentes de UI
        self.img_view = ft.Image(
            src="assets/desactivar-camara.png",
            width=640,
            height=480,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
        )
        
        self.status_text = ft.Text(
            value="Estado: Esperando...",
            size=16,
            color=ft.Colors.BLUE,
        )
        
        self.cedula_text = ft.Text(
            value="Cédula: No detectada",
            size=20,
            weight=ft.FontWeight.BOLD,
        )
        
        # Botones de control
        btn_iniciar = ft.ElevatedButton(
            text="Iniciar Escaneo",
            icon=ft.Icons.CAMERA_ALT,
            on_click=self.on_iniciar_escaneo,
        )
        
        btn_detener = ft.ElevatedButton(
            text="Detener Escaneo",
            icon=ft.Icons.STOP,
            on_click=self.on_detener_escaneo,
        )
        self.inicializar_componentes_gestion()

        # Pestaña de escaneo
        tab_escaneo = ft.Tab(
            text="Escaneo",
            icon=ft.Icons.DOCUMENT_SCANNER,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [btn_iniciar, btn_detener],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Container(height=10),
                        self.status_text,
                        self.cedula_text,
                        ft.Container(height=10),
                        self.img_view,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
            ),
        )
        
        # Pestaña de configuración
        tab_crear = ft.Tab(
            text="Crear Registro",
            icon=ft.Icons.ADD_CIRCLE,
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Nuevo Registro", size=20),
                    self.nombre_input,
                    self.cedula_input,
                    self.especialidad_input,
                    self.anio_input,
                    self.seccion_input,
                    ft.ElevatedButton(
                        "Crear Registro", 
                        on_click=self.crear_click,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLUE
                        )
                    )
                ]),
                padding=15
            )
        )

        # Pestaña de ver todos los registros
        tab_listar = ft.Tab(
            text="Ver Todos los Registros",
            icon=ft.Icons.LIST_ALT,
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Listado de Registros", size=20),
                    ft.ElevatedButton("Refrescar Listado", on_click=lambda _: self.cargar_registros()),
                    self.tabla_registros
                ]),
                padding=15
            )
        )
        # Pestaña de buscar y administrar
        tab_buscar = ft.Tab(
            text="Buscar y Administrar",
            icon=ft.Icons.SEARCH,
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Buscar por Cédula", size=20),
                    ft.Row([
                        self.buscar_cedula_input,
                        ft.ElevatedButton("Buscar", on_click=self.buscar_click)
                    ]),
                    self.resultado_container,
                    ft.Row([
                        ft.ElevatedButton(
                            "Eliminar Registro", 
                            on_click=self.eliminar_click,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_400
                            )
                        ),
                        ft.ElevatedButton(
                            "Actualizar con Datos del Formulario", 
                            on_click=self.actualizar_click,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.ORANGE
                            )
                        )
                    ])
                ]),
                padding=15
            )
        )
        
        # Crear TabView con las pestañas
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[tab_escaneo, tab_crear, tab_buscar, tab_listar],
            expand=True,
        )
        
        # Agregar el TabView a la página
        page.add(tabs)
        self.cargar_registros()
        
    def inicializar_componentes_gestion(self):
        """Inicializa los componentes para gestión de registros"""
        # Campos para el formulario
        self.nombre_input = ft.TextField(label="Nombre del Estudiante", width=400)
        self.cedula_input = ft.TextField(label="Número de Cédula", width=400)
        self.especialidad_input = ft.TextField(label="Especialidad", width=400)
        self.anio_input = ft.TextField(label="Año", width=400)
        self.seccion_input = ft.TextField(label="Sección", width=400)
        self.buscar_cedula_input = ft.TextField(label="Buscar por Cédula", width=400)

        # Contenedor para mostrar los resultados
        self.resultado_container = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            width=750,
            height=250,
            visible=False
        )

        # Tabla para mostrar registros
        self.tabla_registros = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Cédula")),
                ft.DataColumn(ft.Text("Especialidad")),
                ft.DataColumn(ft.Text("Año")),
                ft.DataColumn(ft.Text("Sección")),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_400),
        )

        # Mensaje de estado
        self.mensaje_estado = ft.Text("", color=ft.Colors.BLACK, size=16)
    
    # Métodos para el escáner de cédula
    def on_iniciar_escaneo(self, e):
        """Manejador del evento de clic en el botón Iniciar"""
        if self.escaner is None:
            self.status_text.value = "Estado: Inicializando cámara y OCR..."
            self.status_text.color = ft.Colors.ORANGE
            self.cedula_text.value = "Cédula: Buscando..."
            self.update_ui()
            self.detenido = False
            # Crear y configurar el escáner
            if not self.escaner:
                self.escaner = EscanerCedula(
                    on_cedula_found=self.on_cedula_found,
                    on_scan_failed=self.on_scan_failed,
                    on_frame_update=self.on_frame_update
                )
            if self.escaner:
                print(self.escaner)
            # Iniciar escaneo en un hilo separado
            self.escaner.iniciar_escaneo()
    
    def on_detener_escaneo(self, e):
        """Manejador del evento de clic en el botón Detener"""
        if self.escaner:
            self.detenido = True
            self.escaner.detener_escaneo()
            self.status_text.value = "Estado: Escaneo detenido"
            self.status_text.color = ft.Colors.RED
            self.cedula_text.value = "Cédula: No detectada"
            self.escaner = None
            self.restablecer_imagen()
            
            self.update_ui()
            
    def restablecer_imagen(self):
        """Método auxiliar para restablecer la imagen a su estado original"""
        if self.img_view:
            self.img_view.src = "desactivar-camara.png"
            self.img_view.src_base64 = None
            

    def on_cedula_found(self, cedula):
        """Callback cuando se encuentra una cédula"""
        print(f"[INFO] Mostrando modal para cédula: {cedula}")
        if not self.page:
            print("[ERROR] self.page no está inicializado")
            return
            
        # Actualizar textos en la interfaz
        self.cedula_encontrada = cedula
        self.status_text.value = "Estado: ¡Cédula detectada!"
        self.status_text.color = ft.Colors.GREEN
        self.cedula_text.value = f"Cédula: {cedula}"
        
        # Pausar el escaneo temporalmente
        if self.escaner:
            self.escaner.detener_escaneo()
        
        is_registered = gestor.buscar_por_cedula(cedula)
        if is_registered:
            # Crear el diálogo modal con todos los datos del estudiante
            modal_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Estudiante Registrado", size=24, weight=ft.FontWeight.BOLD),
                content=ft.Column(
                    [
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("INFORMACIÓN DEL ESTUDIANTE", 
                                            weight=ft.FontWeight.BOLD, 
                                            size=18,
                                            color=ft.Colors.BLUE),
                                        ft.Divider(),
                                        
                                        # Nombre del estudiante
                                        ft.Text("Nombre:", size=16),
                                        ft.Text(
                                            is_registered["nombre_estudiante"], 
                                            size=20, 
                                            weight=ft.FontWeight.BOLD,
                                            selectable=True
                                        ),
                                        ft.Divider(height=10, thickness=0.5),
                                        
                                        # Número de cédula
                                        ft.Text("Número de Cédula:", size=16),
                                        ft.Text(
                                            is_registered["numero_de_cedula"], 
                                            size=20, 
                                            weight=ft.FontWeight.BOLD, 
                                            color=ft.Colors.GREEN,
                                            selectable=True
                                        ),
                                        ft.Divider(height=10, thickness=0.5),
                                        
                                        # Especialidad
                                        ft.Text("Especialidad:", size=16),
                                        ft.Text(
                                            is_registered["especialidad"], 
                                            size=20, 
                                            weight=ft.FontWeight.BOLD,
                                            selectable=True
                                        ),
                                        ft.Divider(height=10, thickness=0.5),
                                        
                                        # Año
                                        ft.Text("Año:", size=16),
                                        ft.Text(
                                            is_registered["año"], 
                                            size=20, 
                                            weight=ft.FontWeight.BOLD,
                                            selectable=True
                                        ),
                                        ft.Divider(height=10, thickness=0.5),
                                        
                                        # Sección
                                        ft.Text("Sección:", size=16),
                                        ft.Text(
                                            is_registered["sección"], 
                                            size=20, 
                                            weight=ft.FontWeight.BOLD,
                                            selectable=True
                                        ),
                                        ft.Divider(height=10, thickness=0.5),
                                        
                                        # Código Hash
                                        ft.Text("Código Hash:", size=16),
                                        ft.Text(
                                            is_registered["codigo_hash"], 
                                            size=14, 
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_GREY,
                                            selectable=True
                                        ),
                                    ],
                                    spacing=5,
                                    horizontal_alignment=ft.CrossAxisAlignment.START,
                                ),
                                padding=20,
                                border_radius=10,
                            ),
                            elevation=5,
                        ),
                    ],
                    tight=True,
                ),
                actions=[
                    ft.TextButton("Continuar Escaneando", on_click=lambda e: self.page.close(modal_dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                on_dismiss=lambda e: self.on_detener_escaneo(e),
            )
            sonido = pygame.mixer.Sound('assets/success.mp3')
        else:
            # Mostrar diálogo de cédula no registrada
            modal_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Alerta", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                content=ft.Column(
                    [
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(
                                            name=ft.Icons.WARNING_ROUNDED,
                                            color=ft.Colors.RED,
                                            size=64,
                                        ),
                                        ft.Text(
                                            "Cédula no registrada",
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            f"El número {cedula} no está en el sistema",
                                            size=16,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ],
                                    spacing=10,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=20,
                                border_radius=10,
                            ),
                            elevation=5,
                        ),
                    ],
                    tight=True,
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda e: self.page.close(modal_dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                on_dismiss=lambda e: self.page.close(modal_dlg),
            )
            sonido = pygame.mixer.Sound('assets/wrong.mp3')
        self.page.open(modal_dlg)
        sonido.play()
    
    def on_scan_failed(self):
        """Callback cuando no se encuentra una cédula"""
        pass  # No hacemos nada especial aquí para evitar actualizar la UI constantemente
    
    def on_frame_update(self, img_bytes):
        """Callback cuando hay un nuevo frame disponible"""
        if self.img_view and not self.detenido:
            # Convertir bytes a base64 para mostrar en la imagen
            base64_img = base64.b64encode(img_bytes).decode('utf-8')
            self.img_view.src_base64 = base64_img
            self.update_ui()
    
    # Métodos para gestión de registros
    def mostrar_mensaje(self, texto, color=ft.Colors.BLACK):
        """Muestra un mensaje de estado en la interfaz"""
        self.mensaje_estado.value = texto
        self.mensaje_estado.color = color
        self.page.update()
    
    def limpiar_formulario(self):
        """Limpia los campos del formulario"""
        self.nombre_input.value = ""
        self.cedula_input.value = ""
        self.especialidad_input.value = ""
        self.anio_input.value = ""
        self.seccion_input.value = ""
        self.page.update()
    
    def validar_campos_crear(self):
        """Valida que todos los campos obligatorios estén completos"""
        if not self.nombre_input.value or not self.cedula_input.value or not self.especialidad_input.value or not self.anio_input.value or not self.seccion_input.value:
            self.mostrar_mensaje("Todos los campos son obligatorios", ft.Colors.RED)
            return False
        return True
    
    def crear_click(self, e):
        """Manejador para crear un nuevo registro"""
        if not self.validar_campos_crear():
            return
        
        try:
            resultado = gestor.crear_registro(
                self.nombre_input.value,
                self.cedula_input.value,
                self.especialidad_input.value,
                self.anio_input.value,
                self.seccion_input.value
            )
            
            if resultado:
                self.mostrar_mensaje("Registro creado exitosamente", ft.Colors.GREEN)
                self.limpiar_formulario()
                self.cargar_registros()
            else:
                self.mostrar_mensaje("Error al crear el registro", ft.Colors.RED)
        except Exception as ex:
            self.mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED)
    
    def cargar_registros(self):
        """Carga todos los registros en la tabla"""
        try:
            registros = gestor.listar_registros()
            
            # Limpiar filas existentes
            self.tabla_registros.rows.clear()
            
            # Agregar nuevas filas
            for reg in registros:
                self.tabla_registros.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(reg['nombre_estudiante'])),
                            ft.DataCell(ft.Text(reg['numero_de_cedula'])),
                            ft.DataCell(ft.Text(reg['especialidad'])),
                            ft.DataCell(ft.Text(reg['año'])),
                            ft.DataCell(ft.Text(reg['sección'])),
                        ]
                    )
                )
            
            self.page.update()
        except Exception as ex:
            self.mostrar_mensaje(f"Error al cargar registros: {str(ex)}", ft.Colors.RED)
    
    def buscar_click(self, e):
        """Manejador para buscar un registro por cédula"""
        if not self.buscar_cedula_input.value:
            self.mostrar_mensaje("Ingrese un número de cédula para buscar", ft.Colors.RED)
            return
        
        try:
            resultado = gestor.buscar_por_cedula(self.buscar_cedula_input.value)
            
            self.resultado_container.content.controls.clear()
            
            if resultado:
                self.resultado_container.visible = True
                self.resultado_container.content.controls.append(
                    ft.Column([
                        ft.Text(f"Nombre: {resultado['nombre_estudiante']}", size=16),
                        ft.Text(f"Cédula: {resultado['numero_de_cedula']}", size=16),
                        ft.Text(f"Especialidad: {resultado['especialidad']}", size=16),
                        ft.Text(f"Año: {resultado['año']}", size=16),
                        ft.Text(f"Sección: {resultado['sección']}", size=16),
                        ft.Text(f"Código Hash: {resultado['codigo_hash']}", size=14),
                    ])
                )
                self.mostrar_mensaje("Registro encontrado", ft.Colors.GREEN)
            else:
                self.resultado_container.visible = True
                self.resultado_container.content.controls.append(
                    ft.Text("No se encontró ningún registro con esa cédula", size=16, color=ft.Colors.RED)
                )
                self.mostrar_mensaje("No se encontró el registro", ft.Colors.ORANGE)
            
            self.page.update()
        except Exception as ex:
            self.mostrar_mensaje(f"Error en la búsqueda: {str(ex)}", ft.Colors.RED)
    
    def eliminar_click(self, e):
        """Manejador para eliminar un registro por cédula"""
        if not self.buscar_cedula_input.value:
            self.mostrar_mensaje("Ingrese un número de cédula para eliminar", ft.Colors.RED)
            return
        
        try:
            resultado = gestor.eliminar_registro(self.buscar_cedula_input.value)
            
            if resultado:
                self.mostrar_mensaje("Registro eliminado exitosamente", ft.Colors.GREEN)
                self.resultado_container.visible = False
                self.buscar_cedula_input.value = ""
                self.cargar_registros()
            else:
                self.mostrar_mensaje("No se pudo eliminar el registro", ft.Colors.RED)
            
            self.page.update()
        except Exception as ex:
            self.mostrar_mensaje(f"Error al eliminar: {str(ex)}", ft.Colors.RED)
    
    def actualizar_click(self, e):
        """Manejador para actualizar un registro existente"""
        if not self.buscar_cedula_input.value:
            self.mostrar_mensaje("Primero busque un registro para actualizar", ft.Colors.RED)
            return
        
        try:
            datos_actualizados = {}
            
            if self.nombre_input.value:
                datos_actualizados["nombre_estudiante"] = self.nombre_input.value
            if self.especialidad_input.value:
                datos_actualizados["especialidad"] = self.especialidad_input.value
            if self.anio_input.value:
                datos_actualizados["año"] = self.anio_input.value
            if self.seccion_input.value:
                datos_actualizados["sección"] = self.seccion_input.value
            
            if not datos_actualizados:
                self.mostrar_mensaje("No hay datos para actualizar", ft.Colors.ORANGE)
                return
            
            resultado = gestor.actualizar_registro(self.buscar_cedula_input.value, datos_actualizados)
            
            if resultado:
                self.mostrar_mensaje("Registro actualizado exitosamente", ft.Colors.GREEN)
                self.limpiar_formulario()
                self.buscar_cedula_input.value = ""
                self.resultado_container.visible = False
                self.cargar_registros()
            else:
                self.mostrar_mensaje("No se pudo actualizar el registro", ft.Colors.RED)
            
            self.page.update()
        except Exception as ex:
            self.mostrar_mensaje(f"Error al actualizar: {str(ex)}", ft.Colors.RED)
    
    def update_ui(self):
        """Actualiza componentes específicos de la interfaz de usuario"""
        if self.img_view:
            self.img_view.update()
        if self.status_text:
            self.status_text.update()
        if self.cedula_text:
            self.cedula_text.update()


def main():
    app = CedulaApp()
    # Usar view para asegurar que los diálogos funcionen correctamente
    ft.app(target=app.iniciar_app, view=ft.AppView.FLET_APP)

# Ejecución principal
if __name__ == "__main__":
    main()