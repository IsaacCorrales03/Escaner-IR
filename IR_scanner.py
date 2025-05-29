import cv2
import easyocr
import numpy as np
import threading
import time
from typing import Callable
from PIL import Image
from io import BytesIO
import queue

class EscanerCedula:
    def __init__(self, on_cedula_found: Callable[[str], None], on_scan_failed: Callable[[], None], on_frame_update: Callable[[bytes], None]):
        self.reader = None
        self.cap = None
        self.running = False
        self.frame = None
        self.on_cedula_found = on_cedula_found
        self.on_scan_failed = on_scan_failed
        self.on_frame_update = on_frame_update
        
        # Configuración de performance
        self.target_fps = 30
        self.frame_delay = 1.0 / self.target_fps
        
        # Sistema de colas para procesamiento asíncrono
        self.ocr_queue = queue.Queue(maxsize=2)  # Buffer pequeño para evitar acumulación
        self.ocr_thread = None
        self.ocr_running = False
        
        # Cache y optimizaciones
        self.last_ocr_time = 0
        self.ocr_interval = 0.25  # Procesar OCR cada 250ms
        self.frame_skip_counter = 0
        self.frame_skip_rate = 2  # Procesar 1 de cada 3 frames para OCR
        
        # Configuración de imagen
        self.resize_factor = 0.6  # Reducir tamaño para procesamiento
        self.jpeg_quality = 70  # Reducir calidad para transmisión más rápida

    def inicializar(self):
        """Inicializa el lector OCR y la cámara con configuraciones optimizadas"""
        print("[INFO] Iniciando EasyOCR...")
        # Inicializar EasyOCR con configuraciones de performance
        self.reader = easyocr.Reader(['es'], gpu=True)  # Usar GPU si está disponible
        
        print("[INFO] Iniciando cámara...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("No se pudo abrir la cámara")
        
        # Optimizar configuración de la cámara
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para reducir latencia
        
        return True

    def liberar_recursos(self):
        """Libera los recursos de la cámara y detiene hilos"""
        self.ocr_running = False
        if self.ocr_thread and self.ocr_thread.is_alive():
            self.ocr_thread.join(timeout=1.0)
            
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def iniciar_escaneo(self):
        """Inicia los hilos de escaneo"""
        if self.running:
            return
        
        self.running = True
        self.ocr_running = True
        
        # Iniciar hilo de procesamiento OCR separado
        self.ocr_thread = threading.Thread(target=self._loop_ocr, daemon=True)
        self.ocr_thread.start()
        
        # Iniciar hilo principal de captura
        threading.Thread(target=self._loop_captura, daemon=True).start()

    def detener_escaneo(self):
        """Detiene todos los hilos de escaneo"""
        self.running = False
        self.ocr_running = False

    def _loop_captura(self):
        """Loop principal de captura de frames - optimizado para velocidad"""
        if not self.inicializar():
            return
        
        last_frame_time = time.time()
        
        while self.running:
            start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("[ERROR] No se pudo leer el frame.")
                time.sleep(0.01)
                continue

            self.frame = frame
            
            # Enviar frame para OCR solo ocasionalmente
            current_time = time.time()
            if (current_time - self.last_ocr_time > self.ocr_interval and 
                self.frame_skip_counter % self.frame_skip_rate == 0):
                
                self.last_ocr_time = current_time
                # Enviar frame reducido para procesamiento OCR
                frame_pequeno = self._redimensionar_frame_para_ocr(frame)
                
                try:
                    self.ocr_queue.put_nowait(frame_pequeno)
                except queue.Full:
                    # Si la cola está llena, descartar frame antiguo
                    try:
                        self.ocr_queue.get_nowait()
                        self.ocr_queue.put_nowait(frame_pequeno)
                    except queue.Empty:
                        pass
            
            self.frame_skip_counter += 1
            
            # Enviar frame a UI de forma asíncrona
            threading.Thread(target=self._enviar_frame_a_ui, daemon=True).start()
            
            # Control de FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_delay - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.liberar_recursos()

    def _loop_ocr(self):
        """Loop separado para procesamiento OCR"""
        while self.ocr_running:
            try:
                # Esperar por frame para procesar
                frame = self.ocr_queue.get(timeout=0.1)
                self._procesar_frame_ocr(frame)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Error en loop OCR: {e}")

    def _redimensionar_frame_para_ocr(self, frame):
        """Redimensiona el frame para procesamiento OCR más rápido"""
        height, width = frame.shape[:2]
        new_width = int(width * self.resize_factor)
        new_height = int(height * self.resize_factor)
        return cv2.resize(frame, (new_width, new_height))

    def _enviar_frame_a_ui(self):
        """Convierte el frame actual a base64 y lo envía a la UI - optimizado"""
        try:
            if self.frame is None:
                return
                
            # Convertir el frame de OpenCV a formato adecuado para Flet
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            
            # Redimensionar para transmisión más rápida si es necesario
            height, width = rgb_frame.shape[:2]
            if width > 800:
                scale = 800 / width
                new_width = 800
                new_height = int(height * scale)
                rgb_frame = cv2.resize(rgb_frame, (new_width, new_height))
            
            pil_img = Image.fromarray(rgb_frame)
            
            # Convertir a JPEG con calidad optimizada
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
            img_bytes = buffer.getvalue()
            
            # Llamar al callback con los bytes de la imagen
            self.on_frame_update(img_bytes)
        except Exception as e:
            print(f"[ERROR] Error enviando frame a UI: {e}")

    def _procesar_frame_ocr(self, frame):
        """Procesa el frame buscando números de cédula - versión optimizada"""
        try:
            # Preprocesar imagen para mejor OCR
            frame_procesado = self._preprocesar_para_ocr(frame)
            
            # Ejecutar OCR con configuraciones optimizadas
            resultados = self.reader.readtext(
                frame_procesado,
                width_ths=0.7,
                height_ths=0.7,
                paragraph=False,
                detail=1
            )
            
            cedula_encontrada = False
            
            for bbox, texto, conf in resultados:
                texto_limpio = ''.join(filter(str.isdigit, texto))
                
                # Verificar si es un número de cédula válido
                if conf >= 0.25 and len(texto_limpio) == 9:
                    print(f"[DEBUG] Cédula detectada: '{texto_limpio}' (confianza: {conf:.2f})")
                    
                    # Escalar bbox de vuelta al tamaño original
                    bbox_escalado = self._escalar_bbox(bbox, 1/self.resize_factor)
                    self._dibujar_deteccion(bbox_escalado, texto_limpio)
                    
                    # Notificar cédula encontrada
                    threading.Thread(
                        target=self.on_cedula_found,
                        args=(texto_limpio,),
                        daemon=True
                    ).start()
                    cedula_encontrada = True
                    break
            
            if not cedula_encontrada:
                self.on_scan_failed()
                
        except Exception as e:
            print(f"[ERROR] Error en procesamiento OCR: {e}")
            self.on_scan_failed()

    def _preprocesar_para_ocr(self, frame):
        """Preprocesa la imagen para mejorar el OCR"""
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro bilateral para reducir ruido manteniendo bordes
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Ajustar contraste usando CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        return enhanced

    def _escalar_bbox(self, bbox, factor):
        """Escala un bounding box por un factor dado"""
        return [[int(punto[0] * factor), int(punto[1] * factor)] for punto in bbox]

    def _dibujar_deteccion(self, bbox, texto):
        """Dibuja la detección en el frame principal"""
        if self.frame is None:
            return
            
        try:
            puntos = [tuple(punto) for punto in bbox]
            cv2.polylines(self.frame, [np.array(puntos)], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.putText(self.frame, texto, puntos[0], cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        except Exception as e:
            print(f"[ERROR] Error dibujando detección: {e}")

    def ajustar_parametros_performance(self, target_fps=51, ocr_interval=0, resize_factor=0):
        """Permite ajustar parámetros de performance en tiempo real"""
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self.ocr_interval = ocr_interval
        self.resize_factor = resize_factor
