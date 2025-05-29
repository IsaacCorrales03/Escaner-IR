import sqlite3
import os

def crear_base_de_datos(nombre_db="cedulas.db"):
    """
    Crea la base de datos SQLite y las tablas para el sistema de registro de cédulas.
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
            ruta_img_estudiante TEXT NOT NULL, 
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(crear_tabla_query)
        print("Tabla 'cedulas_registradas' creada o ya existente")
        
        # Crear tabla historial
        crear_historial_query = """
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_de_cedula TEXT NOT NULL,
            dia DATE NOT NULL,
            hora TIME NOT NULL,
            becado TEXT NOT NULL, 
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(crear_historial_query)
        print("Tabla 'historial' creada o ya existente")
        
        # Crear índices para optimizar búsquedas
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cedula ON cedulas_registradas(numero_de_cedula)")
            print("Índice para número de cédula creado o ya existente")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON cedulas_registradas(codigo_hash)")
            print("Índice para código hash creado o ya existente")
            
            # Índices para la tabla historial
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_cedula ON historial(numero_de_cedula)")
            print("Índice para historial por cédula creado o ya existente")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial(dia)")
            print("Índice para historial por fecha creado o ya existente")
                
        except sqlite3.Error as e:
            print(f"Error al crear índices: {e}")
            
        # Confirmar cambios
        conexion.commit()
        print("Base de datos configurada correctamente")
        
    except sqlite3.Error as e:
        print(f"Error SQLite: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_base_de_datos()
    print("Proceso de creación de base de datos completado")