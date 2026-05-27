#!/usr/bin/env python3
"""
LogiAnalytics Pro - Script de ejecución principal
Ejecuta tanto la aplicación web como la API en paralelo
"""

import subprocess
import sys
import time
import os
from multiprocessing import Process
import signal

def run_streamlit():
    """Ejecuta la aplicación Streamlit"""
    print("🚀 Iniciando aplicación web Streamlit...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false"
    ])

def run_api():
    """Ejecuta la API FastAPI"""
    print("🔌 Iniciando API FastAPI...")
    os.chdir("api")
    subprocess.run([
        sys.executable, "main.py"
    ])

def signal_handler(sig, frame):
    """Maneja señales de interrupción"""
    print("\n🛑 Deteniendo servicios...")
    sys.exit(0)

def main():
    """Función principal"""
    print("""
    🚚 LogiAnalytics Pro - Plataforma de Análisis Logístico
    =====================================================
    
    Iniciando servicios...
    - Aplicación Web: http://localhost:8501
    - API REST: http://localhost:8000
    - Documentación API: http://localhost:8000/docs
    
    Presiona Ctrl+C para detener todos los servicios
    """)
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Crear procesos para ejecutar en paralelo
        streamlit_process = Process(target=run_streamlit)
        api_process = Process(target=run_api)
        
        # Iniciar procesos
        streamlit_process.start()
        time.sleep(2)  # Esperar un poco para que Streamlit inicie
        api_process.start()
        
        # Esperar a que terminen
        streamlit_process.join()
        api_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        streamlit_process.terminate()
        api_process.terminate()
        streamlit_process.join()
        api_process.join()
        print("✅ Servicios detenidos correctamente")

if __name__ == "__main__":
    main()
