# Sistema de Gestión de Cédulas Estudiantiles

## Descripción General

Este proyecto implementa un sistema para gestionar cédulas estudiantiles mediante una base de datos SQLite. El sistema permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) sobre registros de cédulas estudiantiles, generando un código hash único para cada cédula que facilitará su verificación e identificación.

## Estructura del Proyecto

El proyecto consta de dos archivos principales:

1. **db.py**: Script encargado de crear y configurar la base de datos SQLite.
2. **gestorPrincipal.py**: Implementación principal del sistema con todas las operaciones CRUD.

## Funcionalidades Implementadas

### Base de Datos (db.py)

Este script inicializa la base de datos SQLite con la siguiente estructura:

- **Nombre de la base de datos**: `cedulas.db`
- **Tabla principal**: `cedulas_registradas`
- **Columnas**:
  - `id`: Identificador único autoincremental
  - `nombre_estudiante`: Nombre completo del estudiante
  - `numero_de_cedula`: Número de identificación único
  - `codigo_hash`: Hash SHA-256 generado a partir del número de cédula
  - `especialidad`: Área de especialización del estudiante
  - `año`: Año escolar del estudiante
  - `sección`: Sección del estudiante
  - `fecha_registro`: Fecha y hora de registro (automático)

También se crean índices para optimizar las búsquedas:
- Índice para `numero_de_cedula`
- Índice para `codigo_hash`

### Sistema de Gestión (sistema_cedulas.py)

La clase `GestorCedulas` implementa las siguientes operaciones:

#### 1. Creación de Registros
```python
crear_registro(nombre, cedula, especialidad, anio, seccion)
```
Añade un nuevo registro a la base de datos y genera automáticamente un código hash para la cédula.

#### 2. Búsqueda de Registros
```python
buscar_por_cedula(cedula)
```
Busca y retorna un registro específico por su número de cédula.

#### 3. Listado de Registros
```python
listar_registros()
```
Recupera y muestra todos los registros almacenados en la base de datos.

#### 4. Actualización de Registros
```python
actualizar_registro(cedula, datos)
```
Permite modificar los datos de un registro existente identificado por su número de cédula.

#### 5. Eliminación de Registros
```python
eliminar_registro(cedula)
```
Elimina un registro de la base de datos utilizando su número de cédula.

## Tecnologías Utilizadas

- **Python**: Lenguaje de programación principal
- **SQLite**: Sistema de gestión de bases de datos ligero
- **Hashlib**: Biblioteca para generación de códigos hash

## Avances y Planes Futuros

### Estado Actual (50% completado)

- ✅ Implementación completa de operaciones CRUD
- ✅ Generación y almacenamiento de códigos hash para cédulas
- ✅ Base de datos SQLite funcional y optimizada
- ✅ Manejo de errores y excepciones

### Próximas Funcionalidades

#### Integración con Códigos IR

Uno de los principales objetivos a futuro es vincular los códigos IR (Infrarrojo) que están detrás de cada identificación estudiantil con el sistema. Estos códigos se almacenarán y convertirán en códigos hash, los cuales servirán para:

- Verificar la autenticidad de las cédulas
- Simplificar el proceso de registro mediante escaneo
- Crear un sistema de verificación en tiempo real

#### Migración a Base de Datos NoSQL

Para mejorar la escalabilidad y permitir mayor concurrencia de usuarios, se planea migrar el sistema a una base de datos NoSQL:

- Mayor capacidad para manejar grandes volúmenes de datos
- Mejor rendimiento en operaciones de lectura/escritura concurrentes
- Flexibilidad para adaptar el esquema según evolucionen las necesidades
- Capacidad de distribuir la carga entre múltiples servidores

## Instrucciones de Uso

### Requisitos

- Python 3.6 o superior
- Biblioteca SQLite (incluida en Python estándar)

### Instalación

1. Clone este repositorio:
```
git clone https://github.com/tu-usuario/sistema-cedulas.git
cd sistema-cedulas
```

2. No se requieren dependencias adicionales ya que SQLite viene incluido con Python.

### Uso Básico

1. Primero, cree la base de datos:
```
python db.py
```

2. Luego puede ejecutar el sistema:
```
python sistema_cedulas.py
```

3. Para integrar este sistema en su aplicación, puede importar la clase `GestorCedulas`:
```python
from sistema_cedulas import GestorCedulas

gestor = GestorCedulas()
gestor.crear_registro("Nombre", "V12345678", "Especialidad", "3", "A")
```

## Ejemplo de Uso

```python
# Crear instancia del gestor
gestor = GestorCedulas()

# Registrar un estudiante
gestor.crear_registro("Juan Pérez", "V12345678", "Informática", "3", "A")

# Buscar un estudiante
estudiante = gestor.buscar_por_cedula("V12345678")
if estudiante:
    print(f"Encontrado: {estudiante['nombre_estudiante']}")

# Actualizar información
gestor.actualizar_registro("V12345678", {"sección": "B"})

# Listar todos los estudiantes
todos = gestor.listar_registros()
for est in todos:
    print(f"{est['nombre_estudiante']} - {est['especialidad']}")

# Eliminar un registro
gestor.eliminar_registro("V12345678")

# Cerrar conexión
gestor.cerrar_conexion()
```
