import sqlite3
import hashlib
import sys
from datetime import datetime, date, time
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

    # Operaciones CRUD para cédulas
    
    def crear_registro(self, nombre, cedula, especialidad, anio, seccion, ruta_img_estudiante=None):
        """Crea un nuevo registro en la base de datos"""
        try:
            codigo_hash = self.generar_hash(cedula)
            
            # Si no se proporciona ruta de imagen, usar ruta por defecto
            if ruta_img_estudiante is None:
                ruta_img_estudiante = f"assets/images/{cedula}.jpg"
            else:
                # Agregar prefijo si no lo tiene
                if not ruta_img_estudiante.startswith("assets/images/"):
                    ruta_img_estudiante = f"assets/images/{ruta_img_estudiante}"
            
            consulta = """
            INSERT INTO cedulas_registradas 
            (nombre_estudiante, numero_de_cedula, codigo_hash, especialidad, año, sección, ruta_img_estudiante) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            valores = (nombre, cedula, codigo_hash, especialidad, anio, seccion, ruta_img_estudiante)
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
        try:
            consulta = "SELECT * FROM cedulas_registradas"
            self.cursor.execute(consulta)
            registros = self.cursor.fetchall()
            
            if registros:
                resultados = [dict(registro) for registro in registros]
                return resultados
            else:
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

    # Operaciones CRUD para historial
    def agregar_entrada_historial(self, cedula, becado, dia=None, hora=None):
        """
        Agrega una entrada al historial para una cédula.
        Si no se especifica día/hora, usa los valores actuales.
        """
        try:
            # Usar fecha/hora actual si no se especifica
            if dia is None:
                dia = date.today().isoformat()
            if hora is None:
                hora = datetime.now().time().strftime('%H:%M:%S')
            
            consulta = """
            INSERT INTO historial 
            (numero_de_cedula, dia, hora, becado) 
            VALUES (?, ?, ?, ?)
            """
            valores = (cedula, dia, hora, becado)
            self.cursor.execute(consulta, valores)
            self.conexion.commit()
            print(f"Entrada de historial agregada exitosamente. ID: {self.cursor.lastrowid}")
            return True
            
        except sqlite3.Error as e:
            print(f"Error al agregar entrada al historial: {e}")
            return False

    def buscar_historial_por_cedula(self, cedula):
        """Busca todas las entradas del historial para una cédula específica"""
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            consulta = """
            SELECT * FROM historial 
            WHERE numero_de_cedula = ? AND dia = ?
            ORDER BY dia DESC, hora DESC
            """
            self.cursor.execute(consulta, (cedula,hoy))
            registros = self.cursor.fetchall()
            
            if registros:
                return [dict(registro) for registro in registros]
            
            else:
                print("No se encontró historial para esa cédula")
                return []
        except sqlite3.Error as e:
            print(f"Error al buscar historial: {e}")
            return []

    def buscar_historial_por_fecha(self, fecha):
        """Busca todas las entradas del historial para una fecha específica"""
        try:
            consulta = """
            SELECT * FROM historial 
            WHERE dia = ? 
            ORDER BY hora DESC
            """
            self.cursor.execute(consulta, (fecha,))
            registros = self.cursor.fetchall()
            
            if registros:
                return [dict(registro) for registro in registros]
            else:
                print(f"No se encontraron registros para la fecha {fecha}")
                return []
        except sqlite3.Error as e:
            print(f"Error al buscar historial por fecha: {e}")
            return []

    def listar_historial_completo(self):
        """Lista todo el historial ordenado por fecha y hora"""
        try:
            consulta = """
            SELECT * FROM historial 
            ORDER BY dia DESC, hora DESC
            """
            self.cursor.execute(consulta)
            registros = self.cursor.fetchall()
            
            if registros:
                return [dict(registro) for registro in registros]
            else:
                print("No hay registros en el historial")
                return []
        except sqlite3.Error as e:
            print(f"Error al listar historial: {e}")
            return []

    def eliminar_entrada_historial(self, id_historial):
        """Elimina una entrada específica del historial por su ID"""
        try:
            consulta = "DELETE FROM historial WHERE id = ?"
            self.cursor.execute(consulta, (id_historial,))
            self.conexion.commit()
            
            if self.cursor.rowcount > 0:
                print(f"Entrada de historial eliminada exitosamente")
                return True
            else:
                print("No se encontró la entrada del historial para eliminar")
                return False
        except sqlite3.Error as e:
            print(f"Error al eliminar entrada del historial: {e}")
            return False

    def limpiar_historial_por_cedula(self, cedula):
        """Elimina todas las entradas del historial para una cédula específica"""
        try:
            consulta = "DELETE FROM historial WHERE numero_de_cedula = ?"
            self.cursor.execute(consulta, (cedula,))
            self.conexion.commit()
            
            if self.cursor.rowcount > 0:
                print(f"Historial limpiado para la cédula {cedula}. {self.cursor.rowcount} entradas eliminadas")
                return True
            else:
                print("No se encontraron entradas del historial para esa cédula")
                return False
        except sqlite3.Error as e:
            print(f"Error al limpiar historial: {e}")
            return False


# Ejemplo de uso del sistema con historial
if __name__ == "__main__":
        # Crear la única instancia del gestor
        gestor = GestorCedulas()
        
        print(gestor.buscar_historial_por_cedula('120210112'))