import cv2
import easyocr
import numpy as np
import threading
import time
from typing import Callable
from PIL import Image
from io import BytesIO

class EscanerCedula:
    def __init__(self, on_cedula_found: Callable[[str], None], on_scan_failed: Callable[[], None], on_frame_update: Callable[[bytes], None]):
        self.reader = None
        self.cap = None
        self.running = False
        self.frame = None
        self.on_cedula_found = on_cedula_found
        self.on_scan_failed = on_scan_failed
        self.on_frame_update = on_frame_update
        self.last_scan_time = 0
        self.scan_cooldown = 0  # Tiempo en segundos entre escaneos

    def inicializar(self):
        """Inicializa el lector OCR y la cámara"""
        print("[INFO] Iniciando EasyOCR...")
        self.reader = easyocr.Reader(['es'])
        print("[INFO] Iniciando cámara...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("No se pudo abrir la cámara")
        return True

    def liberar_recursos(self):
        """Libera los recursos de la cámara"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def iniciar_escaneo(self):
        """Inicia el hilo de escaneo"""
        if self.running:
            return
        
        self.running = True
        threading.Thread(target=self._loop_escaneo, daemon=True).start()

    def detener_escaneo(self):
        """Detiene el hilo de escaneo"""
        self.running = False

    def _loop_escaneo(self):
        """Loop principal de escaneo"""
        if not self.inicializar():
            return
        
        while self.running:
            ret, self.frame = self.cap.read()
            if not ret or self.frame is None:
                print("[ERROR] No se pudo leer el frame.")
                time.sleep(0.1)
                continue

            # Procesamiento del frame
            current_time = time.time()
            if current_time - self.last_scan_time > self.scan_cooldown:
                self._procesar_frame()
                self.last_scan_time = current_time
            
            # Convertir frame para enviar a Flet
            self._enviar_frame_a_ui()
            
            # Pequeño delay para no saturar la CPU
            time.sleep(0.03)
        
        self.liberar_recursos()

    def _enviar_frame_a_ui(self):
        """Convierte el frame actual a base64 y lo envía a la UI"""
        try:
            # Convertir el frame de OpenCV a formato adecuado para Flet
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            
            # Convertir a JPEG y luego a base64
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG", quality=80)
            img_bytes = buffer.getvalue()
            
            # Llamar al callback con los bytes de la imagen
            self.on_frame_update(img_bytes)
        except Exception as e:
            print(f"[ERROR] Error enviando frame a UI: {e}")

    def _procesar_frame(self):
        """Procesa el frame actual buscando números de cédula"""
        print("[INFO] Analizando frame...")
        try:
            resultados = self.reader.readtext(self.frame)
            
            for bbox, texto, conf in resultados:
                texto_limpio = texto.replace(' ', '')
                
                # Verificar si es un número de cédula válido (9 dígitos y buena confianza)
                if conf >= 0.60 and len(texto_limpio) == 9 and texto_limpio.isdigit():
                    print(f"[DEBUG] Cédula detectada: '{texto_limpio}' (confianza: {conf:.2f})")
                    
                    # Dibujar bounding box
                    (tl, tr, br, bl) = bbox
                    puntos = [tuple(map(int, tl)), tuple(map(int, tr)), tuple(map(int, br)), tuple(map(int, bl))]
                    cv2.polylines(self.frame, [np.array(puntos)], isClosed=True, color=(0, 255, 0), thickness=2)
                    cv2.putText(self.frame, texto_limpio, puntos[0], cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    # Notificar al callback con la cédula encontrada
                    # Usamos threading para evitar bloqueos en la UI
                    threading.Thread(
                        target=self.on_cedula_found,
                        args=(texto_limpio,),
                        daemon=True
                    ).start()
                    return
            
            # Si no se encontró ninguna cédula válida
            self.on_scan_failed()
                
        except Exception as e:
            print(f"[ERROR] Error en procesamiento OCR: {e}")
            self.on_scan_failed()

