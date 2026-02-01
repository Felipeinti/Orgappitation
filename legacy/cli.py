#!/usr/bin/env python3
"""
CLI para agregar transacciones usando YAML
"""
import sys
import yaml
from pathlib import Path
from typing import Optional
from datetime import datetime
from decimal import Decimal

from models import Transaccion, PrecioReferencia
from database import DatabaseManager


class FinanzasCLI:
    """CLI para gestionar finanzas"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def agregar_desde_yaml(self, yaml_string: str) -> bool:
        """
        Agregar transacción desde string YAML
        
        Ejemplo minimo:
        monto: 100
        
        Ejemplo completo:
        monto: 5000
        moneda: ARS
        tipo_gasto: variable
        metodo_pago: tarjeta_credito
        fuente_dinero: Tarjeta Canadá
        descripcion: Cena en restaurante
        categoria: comida
        """
        try:
            # Parsear YAML
            data = yaml.safe_load(yaml_string)
            
            if not data:
                print("❌ El YAML está vacío")
                return False
            
            # Validar que al menos tenga monto
            if 'monto' not in data:
                print("❌ Debes especificar al menos el campo 'monto'")
                return False
            
            # Convertir monto a Decimal
            data['monto'] = Decimal(str(data['monto']))
            
            # Crear transacción
            transaccion = Transaccion(**data)
            
            # Guardar en base de datos
            if self.db.agregar_transaccion(transaccion):
                print(f"✅ Transacción agregada exitosamente!")
                print(f"   ID: {transaccion.id}")
                print(f"   Monto: {transaccion.monto} {transaccion.moneda.value}")
                if transaccion.descripcion:
                    print(f"   Descripción: {transaccion.descripcion}")
                return True
            else:
                print("❌ Error al guardar la transacción")
                return False
                
        except yaml.YAMLError as e:
            print(f"❌ Error al parsear YAML: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def agregar_precio_desde_yaml(self, yaml_string: str) -> bool:
        """
        Agregar precio de referencia desde YAML
        
        Ejemplo:
        simbolo: USD
        precio: 1050.50
        fuente: Dólar Blue
        """
        try:
            data = yaml.safe_load(yaml_string)
            
            if not data:
                print("❌ El YAML está vacío")
                return False
            
            # Validar campos requeridos
            if 'simbolo' not in data or 'precio' not in data:
                print("❌ Debes especificar 'simbolo' y 'precio'")
                return False
            
            data['precio'] = Decimal(str(data['precio']))
            
            precio = PrecioReferencia(**data)
            
            if self.db.agregar_precio_referencia(precio):
                print(f"✅ Precio agregado exitosamente!")
                print(f"   {precio.simbolo}: {precio.precio} ARS")
                return True
            else:
                print("❌ Error al guardar el precio")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def mostrar_ultimas_transacciones(self, n: int = 10):
        """Mostrar últimas N transacciones"""
        transacciones = self.db.leer_transacciones()
        
        if not transacciones:
            print("📊 No hay transacciones registradas")
            return
        
        print(f"\n📊 Últimas {min(n, len(transacciones))} transacciones:")
        print("-" * 80)
        
        for t in transacciones[-n:]:
            fecha = t['fecha'][:16]  # Solo fecha y hora
            monto = f"{t['monto']} {t['moneda']}"
            desc = t.get('descripcion', 'Sin descripción')
            print(f"{fecha} | {monto:>15} | {desc}")
        
        print("-" * 80)
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas básicas"""
        stats = self.db.obtener_estadisticas()
        
        print("\n📈 Estadísticas:")
        print("-" * 40)
        print(f"Total transacciones: {stats['total_transacciones']}")
        
        if stats['total_transacciones'] > 0:
            print(f"Total gastos: ${stats['total_gastos']:.2f}")
            print(f"Total ingresos: ${stats['total_ingresos']:.2f}")
            print(f"Balance: ${stats['balance']:.2f}")
        
        print("-" * 40)
    
    def modo_interactivo(self):
        """Modo interactivo para agregar transacciones"""
        print("\n💰 Modo interactivo - Agregar transacción")
        print("Escribe tu YAML (finaliza con una línea vacía):")
        print("Ejemplo mínimo: monto: 100")
        print("-" * 40)
        
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        
        yaml_string = '\n'.join(lines)
        
        if yaml_string.strip():
            self.agregar_desde_yaml(yaml_string)


def main():
    """Función principal del CLI"""
    cli = FinanzasCLI()
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "add":
            # Modo interactivo
            cli.modo_interactivo()
        
        elif comando == "stats":
            # Mostrar estadísticas
            cli.mostrar_estadisticas()
        
        elif comando == "list":
            # Listar transacciones
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            cli.mostrar_ultimas_transacciones(n)
        
        elif comando == "precio":
            # Agregar precio de referencia
            cli.modo_interactivo_precio()
        
        elif comando == "help":
            mostrar_ayuda()
        
        else:
            print(f"❌ Comando desconocido: {comando}")
            mostrar_ayuda()
    else:
        mostrar_ayuda()


def mostrar_ayuda():
    """Mostrar ayuda del CLI"""
    print("""
💰 Finanzas CLI - Gestión de finanzas personales

Uso: python cli.py [comando]

Comandos disponibles:
  add       Agregar una transacción (modo interactivo)
  stats     Mostrar estadísticas
  list [N]  Listar últimas N transacciones (default: 10)
  help      Mostrar esta ayuda

Ejemplos de YAML:

  # Mínimo (solo monto)
  monto: 100

  # Con más detalles
  monto: 5000
  moneda: ARS
  descripcion: Cena en restaurante
  categoria: comida
  tipo_gasto: variable
  metodo_pago: tarjeta_credito
  fuente_dinero: Tarjeta Canadá

  # Ingreso
  monto: 50000
  es_ingreso: true
  descripcion: Sueldo mensual

Campos disponibles:
  - monto (requerido): Monto de la transacción
  - moneda: ARS, USD, CAD, ETH (default: ARS)
  - tipo_gasto: fijo, variable
  - metodo_pago: efectivo, tarjeta_credito, tarjeta_debito, transferencia, otro
  - fuente_dinero: Texto libre (ej: "Tarjeta Canadá", "MercadoPago")
  - descripcion: Descripción del gasto
  - categoria: Categoría (ej: comida, transporte)
  - notas: Notas adicionales
  - es_ingreso: true/false (default: false)
""")


if __name__ == "__main__":
    main()
