#!/usr/bin/env python3
"""
Script para generar archivos de ejemplo para LogiAnalytics Pro
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generar_ejemplo_costos():
    """Genera un archivo Excel de ejemplo con datos de costos"""
    print("📊 Generando archivo de ejemplo de costos...")
    
    # Crear datos de ejemplo para costos
    data_costos = {
        'Fecha': pd.date_range('2024-01-01', periods=30, freq='D'),
        'Costo_Combustible': np.random.normal(500, 50, 30),
        'Costo_Mano_Obra': np.random.normal(800, 100, 30),
        'Costo_Mantenimiento': np.random.normal(200, 30, 30),
        'Costo_Peaje': np.random.normal(150, 20, 30),
        'Costo_Seguro': np.random.normal(100, 10, 30),
        'Ruta': [f'Ruta_{i%5+1}' for i in range(30)],
        'Vehiculo': [f'Vehículo_{i%3+1}' for i in range(30)]
    }
    
    df_costos = pd.DataFrame(data_costos)
    df_costos.to_excel('ejemplo_costos.xlsx', index=False)
    print("✅ Archivo de ejemplo de costos creado: ejemplo_costos.xlsx")

def generar_ejemplo_inventario():
    """Genera un archivo Excel de ejemplo con datos de inventario"""
    print("📦 Generando archivo de ejemplo de inventario...")
    
    # Crear datos de ejemplo para inventario
    data_inventario = {
        'SKU': [f'SKU_{i:04d}' for i in range(1, 51)],
        'Producto': [f'Producto_{i}' for i in range(1, 51)],
        'Cantidad': np.random.randint(10, 500, 50),
        'Precio_Unitario': np.random.normal(50, 15, 50),
        'Ubicacion': [f'Estante_{i%10+1}' for i in range(50)],
        'Fecha_Entrada': pd.date_range('2024-01-01', periods=50, freq='D'),
        'Fecha_Vencimiento': pd.date_range('2024-06-01', periods=50, freq='D'),
        'Proveedor': [f'Proveedor_{i%5+1}' for i in range(50)],
        'Categoria': [f'Categoría_{i%8+1}' for i in range(50)]
    }
    
    df_inventario = pd.DataFrame(data_inventario)
    df_inventario.to_excel('ejemplo_inventario.xlsx', index=False)
    print("✅ Archivo de ejemplo de inventario creado: ejemplo_inventario.xlsx")

def generar_ejemplo_csv():
    """Genera archivos CSV de ejemplo"""
    print("📄 Generando archivos CSV de ejemplo...")
    
    # Costos CSV
    data_costos = {
        'Fecha': pd.date_range('2024-01-01', periods=15, freq='D'),
        'Costo_Combustible': np.random.normal(500, 50, 15),
        'Costo_Mano_Obra': np.random.normal(800, 100, 15),
        'Costo_Mantenimiento': np.random.normal(200, 30, 15)
    }
    
    df_costos = pd.DataFrame(data_costos)
    df_costos.to_csv('ejemplo_costos.csv', index=False)
    print("✅ Archivo CSV de costos creado: ejemplo_costos.csv")
    
    # Inventario CSV
    data_inventario = {
        'SKU': [f'SKU_{i:04d}' for i in range(1, 21)],
        'Producto': [f'Producto_{i}' for i in range(1, 21)],
        'Cantidad': np.random.randint(10, 500, 20),
        'Precio_Unitario': np.random.normal(50, 15, 20)
    }
    
    df_inventario = pd.DataFrame(data_inventario)
    df_inventario.to_csv('ejemplo_inventario.csv', index=False)
    print("✅ Archivo CSV de inventario creado: ejemplo_inventario.csv")

def main():
    """Función principal"""
    print("🚀 Generando archivos de ejemplo para LogiAnalytics Pro...")
    print("=" * 50)
    
    try:
        generar_ejemplo_costos()
        generar_ejemplo_inventario()
        generar_ejemplo_csv()
        
        print("=" * 50)
        print("🎉 ¡Archivos de ejemplo generados exitosamente!")
        print("\n📁 Archivos creados:")
        print("  - ejemplo_costos.xlsx")
        print("  - ejemplo_inventario.xlsx")
        print("  - ejemplo_costos.csv")
        print("  - ejemplo_inventario.csv")
        print("\n💡 Puedes usar estos archivos para probar la funcionalidad de importación")
        
    except Exception as e:
        print(f"❌ Error al generar archivos: {str(e)}")

if __name__ == "__main__":
    main()
