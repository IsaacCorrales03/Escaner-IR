import flet as ft
from GestorPrincipal import GestorCedulas

def main(page: ft.Page):
    # Configuración de la página
    page.title = "Gestor de Cédulas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 600
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Instancia del gestor de cédulas
    gestor = GestorCedulas()

    # Campos para el formulario
    nombre_input = ft.TextField(label="Nombre del Estudiante", width=400)
    cedula_input = ft.TextField(label="Número de Cédula", width=400)
    especialidad_input = ft.TextField(label="Especialidad", width=400)
    anio_input = ft.TextField(label="Año", width=400)
    seccion_input = ft.TextField(label="Sección", width=400)
    buscar_cedula_input = ft.TextField(label="Buscar por Cédula", width=400)

    # Contenedor para mostrar resultados
    resultado_container = ft.Container(
        content=ft.Column([], scroll=ft.ScrollMode.AUTO),
        padding=10,
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=10,
        width=750,
        height=250,
        visible=False
    )

    # Tabla para mostrar registros
    tabla_registros = ft.DataTable(
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
    mensaje_estado = ft.Text("", color=ft.Colors.BLACK, size=16)

    def mostrar_mensaje(texto, color=ft.Colors.BLACK):
        mensaje_estado.value = texto
        mensaje_estado.color = color
        page.update()

    def limpiar_formulario():
        nombre_input.value = ""
        cedula_input.value = ""
        especialidad_input.value = ""
        anio_input.value = ""
        seccion_input.value = ""
        page.update()

    def validar_campos_crear():
        if not nombre_input.value or not cedula_input.value or not especialidad_input.value or not anio_input.value or not seccion_input.value:
            mostrar_mensaje("Todos los campos son obligatorios", ft.Colors.RED)
            return False
        return True

    def crear_click(e):
        if not validar_campos_crear():
            return
        
        try:
            resultado = gestor.crear_registro(
                nombre_input.value,
                cedula_input.value,
                especialidad_input.value,
                anio_input.value,
                seccion_input.value
            )
            
            if resultado:
                mostrar_mensaje("Registro creado exitosamente", ft.Colors.GREEN)
                limpiar_formulario()
                cargar_registros()
            else:
                mostrar_mensaje("Error al crear el registro", ft.Colors.RED)
        except Exception as ex:
            mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED)

    def cargar_registros():
        try:
            registros = gestor.listar_registros()
            
            # Limpiar filas existentes
            tabla_registros.rows.clear()
            
            # Agregar nuevas filas
            for reg in registros:
                tabla_registros.rows.append(
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
            
            page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error al cargar registros: {str(ex)}", ft.Colors.RED)

    def buscar_click(e):
        if not buscar_cedula_input.value:
            mostrar_mensaje("Ingrese un número de cédula para buscar", ft.Colors.RED)
            return
        
        try:
            resultado = gestor.buscar_por_cedula(buscar_cedula_input.value)
            
            resultado_container.content.controls.clear()
            
            if resultado:
                resultado_container.visible = True
                resultado_container.content.controls.append(
                    ft.Column([
                        ft.Text(f"Nombre: {resultado['nombre_estudiante']}", size=16),
                        ft.Text(f"Cédula: {resultado['numero_de_cedula']}", size=16),
                        ft.Text(f"Especialidad: {resultado['especialidad']}", size=16),
                        ft.Text(f"Año: {resultado['año']}", size=16),
                        ft.Text(f"Sección: {resultado['sección']}", size=16),
                        ft.Text(f"Código Hash: {resultado['codigo_hash']}", size=14),
                    ])
                )
                mostrar_mensaje("Registro encontrado", ft.Colors.GREEN)
            else:
                resultado_container.visible = True
                resultado_container.content.controls.append(
                    ft.Text("No se encontró ningún registro con esa cédula", size=16, color=ft.Colors.RED)
                )
                mostrar_mensaje("No se encontró el registro", ft.Colors.ORANGE)
            
            page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error en la búsqueda: {str(ex)}", ft.Colors.RED)

    def eliminar_click(e):
        if not buscar_cedula_input.value:
            mostrar_mensaje("Ingrese un número de cédula para eliminar", ft.Colors.RED)
            return
        
        try:
            resultado = gestor.eliminar_registro(buscar_cedula_input.value)
            
            if resultado:
                mostrar_mensaje("Registro eliminado exitosamente", ft.Colors.GREEN)
                resultado_container.visible = False
                buscar_cedula_input.value = ""
                cargar_registros()
            else:
                mostrar_mensaje("No se pudo eliminar el registro", ft.Colors.RED)
            
            page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error al eliminar: {str(ex)}", ft.Colors.RED)

    def actualizar_click(e):
        if not buscar_cedula_input.value:
            mostrar_mensaje("Primero busque un registro para actualizar", ft.Colors.RED)
            return
        
        try:
            datos_actualizados = {}
            
            if nombre_input.value:
                datos_actualizados["nombre_estudiante"] = nombre_input.value
            if especialidad_input.value:
                datos_actualizados["especialidad"] = especialidad_input.value
            if anio_input.value:
                datos_actualizados["año"] = anio_input.value
            if seccion_input.value:
                datos_actualizados["sección"] = seccion_input.value
            
            if not datos_actualizados:
                mostrar_mensaje("No hay datos para actualizar", ft.Colors.ORANGE)
                return
            
            resultado = gestor.actualizar_registro(buscar_cedula_input.value, datos_actualizados)
            
            if resultado:
                mostrar_mensaje("Registro actualizado exitosamente", ft.Colors.GREEN)
                limpiar_formulario()
                buscar_cedula_input.value = ""
                resultado_container.visible = False
                cargar_registros()
            else:
                mostrar_mensaje("No se pudo actualizar el registro", ft.Colors.RED)
            
            page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error al actualizar: {str(ex)}", ft.Colors.RED)

    # Diseño de la interfaz
    page.add(
        ft.Text("Sistema Gestor de Cédulas", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        
        # Panel de pestañas
        ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Crear Registro",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Nuevo Registro", size=20),
                            nombre_input,
                            cedula_input,
                            especialidad_input,
                            anio_input,
                            seccion_input,
                            ft.ElevatedButton(
                                "Crear Registro", 
                                on_click=crear_click,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE
                                )
                            )
                        ]),
                        padding=15
                    )
                ),
                ft.Tab(
                    text="Buscar y Administrar",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Buscar por Cédula", size=20),
                            ft.Row([
                                buscar_cedula_input,
                                ft.ElevatedButton("Buscar", on_click=buscar_click)
                            ]),
                            resultado_container,
                            ft.Row([
                                ft.ElevatedButton(
                                    "Eliminar Registro", 
                                    on_click=eliminar_click,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED_400
                                    )
                                ),
                                ft.ElevatedButton(
                                    "Actualizar con Datos del Formulario", 
                                    on_click=actualizar_click,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.ORANGE
                                    )
                                )
                            ])
                        ]),
                        padding=15
                    )
                ),
                ft.Tab(
                    text="Ver Todos los Registros",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Listado de Registros", size=20),
                            ft.ElevatedButton("Refrescar Listado", on_click=lambda _: cargar_registros()),
                            tabla_registros
                        ]),
                        padding=15
                    )
                )
            ]
        ),
        
        ft.Divider(),
        mensaje_estado
    )
    
    # Cargar registros al iniciar
    cargar_registros()


if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")