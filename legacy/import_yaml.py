#!/usr/bin/env python3
"""
Script para importar múltiples transacciones desde un archivo YAML
"""
import sys
import yaml
from pathlib import Path
from decimal import Decimal

from models import Transaccion, PrecioReferencia
from database import DatabaseManager


def importar_transacciones_desde_archivo(filepath: str):
    """
    Importar transacciones desde un archivo YAML
    
    El archivo puede contener una lista de transacciones o una sola transacción
    
    Ejemplo de archivo YAML con múltiples transacciones:
    
    transacciones:
      - monto: 5000
        descripcion: Supermercado
        categoria: comida
      - monto: 200
        descripcion: Café
        metodo_pago: efectivo
      - monto: 50000
        es_ingreso: true
        descripcion: Sueldo
    """
    db = DatabaseManager()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            print("❌ El archivo está vacío")
            return
        
        # Verificar si es una lista de transacciones o una sola
        transacciones = []
        
        if isinstance(data, list):
            # Es una lista directa de transacciones
            transacciones = data
        elif 'transacciones' in data:
            # Tiene una clave 'transacciones'
            transacciones = data['transacciones']
        elif isinstance(data, dict) and 'monto' in data:
            # Es una sola transacción
            transacciones = [data]
        else:
            print("❌ Formato de archivo no reconocido")
            return
        
        # Procesar cada transacción
        exitosas = 0
        errores = 0
        
        for i, t_data in enumerate(transacciones, 1):
            try:
                # Validar que tenga monto
                if 'monto' not in t_data:
                    print(f"⚠️  Transacción {i}: Falta el campo 'monto', omitiendo...")
                    errores += 1
                    continue
                
                # Convertir monto a Decimal
                t_data['monto'] = Decimal(str(t_data['monto']))
                
                # Crear y guardar transacción
                transaccion = Transaccion(**t_data)
                
                if db.agregar_transaccion(transaccion):
                    print(f"✅ Transacción {i}: {transaccion.monto} {transaccion.moneda.value} - {transaccion.descripcion or 'Sin descripción'}")
                    exitosas += 1
                else:
                    print(f"❌ Transacción {i}: Error al guardar")
                    errores += 1
                    
            except Exception as e:
                print(f"❌ Transacción {i}: Error - {e}")
                errores += 1
        
        # Resumen
        print("\n" + "="*60)
        print(f"📊 Resumen de importación:")
        print(f"   ✅ Exitosas: {exitosas}")
        print(f"   ❌ Errores: {errores}")
        print(f"   📝 Total: {exitosas + errores}")
        print("="*60)
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {filepath}")
    except yaml.YAMLError as e:
        print(f"❌ Error al parsear YAML: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


def crear_archivo_ejemplo():
    """Crear un archivo YAML de ejemplo"""
    ejemplo = """# Ejemplo de archivo de transacciones
# Puedes tener múltiples transacciones en un solo archivo

transacciones:
  # Gasto simple
  - monto: 5000
    descripcion: Supermercado Carrefour
    categoria: comida
    tipo_gasto: variable
    metodo_pago: tarjeta_debito
    fuente_dinero: Tarjeta Argentina

  # Gasto con tarjeta de crédito
  - monto: 12000
    descripcion: Cena en restaurante
    categoria: comida
    tipo_gasto: variable
    metodo_pago: tarjeta_credito
    fuente_dinero: Tarjeta Canadá

  # Gasto fijo
  - monto: 45000
    descripcion: Alquiler mes enero
    categoria: vivienda
    tipo_gasto: fijo
    metodo_pago: transferencia

  # Gasto en efectivo
  - monto: 300
    descripcion: Propina
    metodo_pago: efectivo

  # Ingreso
  - monto: 150000
    es_ingreso: true
    descripcion: Sueldo enero
    categoria: trabajo

  # Gasto con MercadoPago
  - monto: 8500
    descripcion: Compra en línea
    categoria: varios
    metodo_pago: transferencia
    fuente_dinero: MercadoPago
"""
    
    with open('ejemplo_transacciones.yaml', 'w', encoding='utf-8') as f:
        f.write(ejemplo)
    
    print("✅ Archivo 'ejemplo_transacciones.yaml' creado!")


def main():
    if len(sys.argv) < 2:
        print("""
💰 Importador de transacciones desde YAML

Uso:
  python import_yaml.py <archivo.yaml>    # Importar desde archivo
  python import_yaml.py ejemplo           # Crear archivo de ejemplo

Formato del archivo YAML:
  
  # Opción 1: Lista directa
  - monto: 100
    descripcion: Café
  - monto: 200
    descripcion: Almuerzo
  
  # Opción 2: Con clave 'transacciones'
  transacciones:
    - monto: 100
      descripcion: Café
    - monto: 200
      descripcion: Almuerzo
  
  # Opción 3: Una sola transacción
  monto: 100
  descripcion: Café
""")
        return
    
    comando = sys.argv[1]
    
    if comando == "ejemplo":
        crear_archivo_ejemplo()
    else:
        importar_transacciones_desde_archivo(comando)


if __name__ == "__main__":
    main()
