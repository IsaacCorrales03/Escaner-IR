import sqlite3
import hashlib
import sys
from threading import Lock
from db import crear_base_de_datos

class GestorCedulas:
    # Variable de clase para almacenar la única instancia
    _instance = None
    # Lock para garantizar thread-safety durante la creación de la instancia
    _lock = Lock()

    def __new__(cls, db_file="cedulas.db"):
        """
        Implementa el patrón Singleton asegurando que solo haya una instancia.
        Thread-safe usando Lock.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GestorCedulas, cls).__new__(cls)
                # Inicializar la instancia solo una vez
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_file="cedulas.db"):
        """
        Inicializa la conexión a la base de datos SQLite solo si no está inicializada.
        """
        if not getattr(self, '_initialized', False):
            try:
                crear_base_de_datos()
                self.conexion = sqlite3.connect(db_file, check_same_thread=False)
                # Configurar para que devuelva filas como diccionarios
                self.conexion.row_factory = sqlite3.Row
                self.cursor = self.conexion.cursor()
                print(f"Conexión exitosa a la base de datos SQLite: {db_file}")
                self._initialized = True
            except sqlite3.Error as e:
                print(f"Error al conectar a SQLite: {e}")
                sys.exit(1)

    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos"""
        if hasattr(self, 'conexion'):
            self.cursor.close()
            self.conexion.close()
            print("Conexión cerrada")
            # Resetear la instancia para permitir reconexión si es necesario
            with self._lock:
                GestorCedulas._instance = None

    def generar_hash(self, numero_cedula):
        """Genera un hash único para la cédula"""
        hash_object = hashlib.sha256(str(numero_cedula).encode())
        return hash_object.hexdigest()

    # Operaciones CRUD
    def crear_registro(self, nombre, cedula, especialidad, anio, seccion):
        """Crea un nuevo registro en la base de datos"""
        try:
            codigo_hash = self.generar_hash(cedula)
            consulta = """
            INSERT INTO cedulas_registradas 
            (nombre_estudiante, numero_de_cedula, codigo_hash, especialidad, año, sección) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
            valores = (nombre, cedula, codigo_hash, especialidad, anio, seccion)
            self.cursor.execute(consulta, valores)
            self.conexion.commit()
            print(f"Registro creado exitosamente. ID: {self.cursor.lastrowid}")
            return True
        except sqlite3.Error as e:
            print(f"Error al crear registro: {e}")
            return False

    def buscar_por_cedula(self, cedula):
        """Busca un registro por número de cédula"""
        try:
            consulta = "SELECT * FROM cedulas_registradas WHERE numero_de_cedula = ?"
            self.cursor.execute(consulta, (cedula,))
            registro = self.cursor.fetchone()
            
            if registro:
                return dict(registro)
            else:
                print("No se encontró ningún registro con esa cédula")
                return None
        except sqlite3.Error as e:
            print(f"Error al buscar registro: {e}")
            return None

    def listar_registros(self):
        """Lista todos los registros de la base de datos"""
        try:
            consulta = "SELECT * FROM cedulas_registradas"
            self.cursor.execute(consulta)
            registros = self.cursor.fetchall()
            
            if registros:
                resultados = [dict(registro) for registro in registros]
                return resultados
            else:
                print("No hay registros en la base de datos")
                return []
        except sqlite3.Error as e:
            print(f"Error al listar registros: {e}")
            return []

    def actualizar_registro(self, cedula, datos):
        """Actualiza un registro existente"""
        try:
            campos_permitidos = ['nombre_estudiante', 'especialidad', 'año', 'sección']
            actualizaciones = []
            valores = []
            
            for campo, valor in datos.items():
                if campo in campos_permitidos:
                    actualizaciones.append(f"{campo} = ?")
                    valores.append(valor)
            
            if not actualizaciones:
                print("No hay campos válidos para actualizar")
                return False
                
            consulta = f"UPDATE cedulas_registradas SET {', '.join(actualizaciones)} WHERE numero_de_cedula = ?"
            valores.append(cedula)
            
            self.cursor.execute(consulta, valores)
            self.conexion.commit()
            
            if self.cursor.rowcount > 0:
                print(f"Registro actualizado exitosamente")
                return True
            else:
                print("No se encontró el registro o no se realizaron cambios")
                return False
        except sqlite3.Error as e:
            print(f"Error al actualizar registro: {e}")
            return False

    def eliminar_registro(self, cedula):
        """Elimina un registro por número de cédula"""
        try:
            consulta = "DELETE FROM cedulas_registradas WHERE numero_de_cedula = ?"
            self.cursor.execute(consulta, (cedula,))
            self.conexion.commit()
            
            if self.cursor.rowcount > 0:
                print(f"Registro eliminado exitosamente")
                return True
            else:
                print("No se encontró el registro para eliminar")
                return False
        except sqlite3.Error as e:
            print(f"Error al eliminar registro: {e}")
            return False


# Ejemplo de uso del sistema
if __name__ == "__main__":
    try:
        # Crear la única instancia del gestor
        gestor = GestorCedulas()
        
        # Ejemplo de creación
        gestor.crear_registro("Juan Pérez", "V12345678", "Informática", "3", "A")
        gestor.crear_registro("María González", "V87654321", "Electrónica", "2", "B")
        
        # Ejemplo de búsqueda
        resultado = gestor.buscar_por_cedula("V12345678")
        if resultado:
            print(f"Estudiante encontrado: {resultado['nombre_estudiante']}")
        
        # Ejemplo de actualización
        gestor.actualizar_registro("V12345678", {"nombre_estudiante": "Juan A. Pérez", "sección": "C"})
        
        # Ejemplo de listado
        print("\nListado de registros:")
        registros = gestor.listar_registros()
        for reg in registros:
            print(f"{reg['nombre_estudiante']} - {reg['numero_de_cedula']} - {reg['especialidad']}")
        
        # Ejemplo de eliminación
        gestor.eliminar_registro("V87654321")
        
        # Cerrar conexión
        gestor.cerrar_conexion()
        
        # Intentar crear otra instancia (debería devolver la misma)
        gestor2 = GestorCedulas()
        print(f"¿Es la misma instancia? {gestor is gestor2}")  # Debería imprimir True
    except Exception as e:
        print(f"Error general: {e}")