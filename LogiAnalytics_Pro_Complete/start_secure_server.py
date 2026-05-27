#!/usr/bin/env python3
"""
LogiAnalytics Pro - Servidor Seguro
Ejecuta el servidor con medidas de seguridad avanzadas
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def print_banner():
    """Muestra el banner de inicio del servidor seguro"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🔒 LOGIANALYTICS PRO - SERVIDOR SEGURO 🔒             ║
    ║                                                              ║
    ║    Plataforma de Análisis Logístico con Seguridad Avanzada   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'sqlite3'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - FALTANTE")
    
    if missing_packages:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
        print("📦 Instalando paquetes faltantes...")
        
        for package in missing_packages:
            if package != 'sqlite3':  # sqlite3 viene con Python
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    print(f"✅ {package} instalado correctamente")
                except subprocess.CalledProcessError:
                    print(f"❌ Error instalando {package}")
                    return False
    
    print("✅ Todas las dependencias están disponibles")
    return True

def start_secure_server():
    """Inicia el servidor seguro de Streamlit"""
    print("\n🚀 Iniciando servidor seguro...")
    
    # Configuración del servidor
    server_config = {
        'port': 8501,
        'headless': True,
        'enableCORS': False,
        'enableXsrfProtection': True
    }
    
    # Comando para ejecutar Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'secure_server.py',
        '--server.port', str(server_config['port']),
        '--server.headless', str(server_config['headless']).lower(),
        '--server.enableCORS', str(server_config['enableCORS']).lower(),
        '--server.enableXsrfProtection', str(server_config['enableXsrfProtection']).lower(),
        '--theme.primaryColor', '#ff6b6b',
        '--theme.backgroundColor', '#ffffff',
        '--theme.secondaryBackgroundColor', '#f0f2f6',
        '--theme.textColor', '#262730'
    ]
    
    try:
        print(f"🌐 Servidor iniciando en puerto {server_config['port']}...")
        print("🔒 Medidas de seguridad activadas:")
        print("   - Autenticación de dos factores")
        print("   - Códigos de seguridad únicos")
        print("   - Monitoreo de intentos de acceso")
        print("   - Encriptación de contraseñas")
        print("   - Logs de seguridad detallados")
        
        # Abrir navegador automáticamente después de 3 segundos
        def open_browser():
            time.sleep(3)
            webbrowser.open(f'http://localhost:{server_config["port"]}')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Ejecutar el servidor
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error iniciando el servidor: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        return True
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def show_credentials():
    """Muestra las credenciales de acceso"""
    print("\n🔐 CREDENCIALES DE ACCESO:")
    print("=" * 50)
    print("👤 Usuario: admin")
    print("🔑 Contraseña: Admin123!")
    print("🔒 Código de Seguridad: [Se genera automáticamente]")
    print("=" * 50)
    print("\n🌐 URL: http://localhost:8501")
    print("📱 La aplicación se abrirá automáticamente en tu navegador")
    print("\n⚠️  IMPORTANTE: Guarda estas credenciales de forma segura")

def main():
    """Función principal"""
    print_banner()
    
    # Verificar dependencias
    if not check_dependencies():
        print("❌ No se pudieron instalar todas las dependencias")
        sys.exit(1)
    
    # Mostrar credenciales
    show_credentials()
    
    # Iniciar servidor
    print("\n" + "="*60)
    print("🚀 INICIANDO SERVIDOR SEGURO...")
    print("="*60)
    
    success = start_secure_server()
    
    if success:
        print("\n✅ Servidor detenido correctamente")
    else:
        print("\n❌ Error en el servidor")
        sys.exit(1)

if __name__ == "__main__":
    main()
