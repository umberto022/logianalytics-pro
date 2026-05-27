#!/usr/bin/env python3
"""
LogiAnalytics Pro - Script de demostración
Ejecuta la aplicación con datos de ejemplo pre-cargados
"""

import subprocess
import sys
import os
import sqlite3
from database import Database

def create_demo_data():
    """Crea datos de demostración en la base de datos"""
    print("🔄 Creando datos de demostración...")
    
    # Inicializar base de datos
    db = Database()
    
    # Crear usuarios de demostración
    demo_users = [
        {
            "username": "admin",
            "email": "admin@logianalytics.com",
            "full_name": "Administrador del Sistema",
            "password": "admin123",
            "role": "admin",
            "company_name": "LogiAnalytics Pro",
            "phone": "+52 55 1234 5678",
            "subscription_plan": "enterprise"
        },
        {
            "username": "gerente1",
            "email": "gerente@empresa.com",
            "full_name": "María García",
            "password": "gerente123",
            "role": "user",
            "company_name": "Empresa Logística S.A.",
            "phone": "+52 55 9876 5432",
            "subscription_plan": "pro"
        },
        {
            "username": "operador1",
            "email": "operador@empresa.com",
            "full_name": "Carlos López",
            "password": "operador123",
            "role": "user",
            "company_name": "Empresa Logística S.A.",
            "phone": "+52 55 5555 1234",
            "subscription_plan": "basic"
        }
    ]
    
    # Crear usuarios si no existen
    for user_data in demo_users:
        existing_user = db.get_user_by_username(user_data["username"])
        if not existing_user:
            db.create_user(**user_data)
            print(f"✅ Usuario creado: {user_data['username']}")
        else:
            print(f"ℹ️ Usuario ya existe: {user_data['username']}")
    
    print("✅ Datos de demostración creados exitosamente")

def main():
    """Función principal"""
    print("""
    🚚 LogiAnalytics Pro - Modo Demostración
    ========================================
    
    Este script creará datos de demostración y ejecutará la aplicación.
    
    Usuarios de demostración disponibles:
    - admin / admin123 (Administrador)
    - gerente1 / gerente123 (Gerente)
    - operador1 / operador123 (Operador)
    
    Iniciando...
    """)
    
    try:
        # Crear datos de demostración
        create_demo_data()
        
        # Ejecutar aplicación
        print("\n🚀 Iniciando aplicación web...")
        print("📱 Abre tu navegador en: http://localhost:8501")
        print("🔐 Usa las credenciales de demostración para iniciar sesión")
        print("\nPresiona Ctrl+C para detener la aplicación\n")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Asegúrate de tener Python y las dependencias instaladas")

if __name__ == "__main__":
    main()
