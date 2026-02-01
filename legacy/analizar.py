#!/usr/bin/env python3
"""
Script para analizar transacciones
"""
import sys
from collections import defaultdict
from decimal import Decimal
from database import DatabaseManager


def analizar_por_categoria():
    """Analizar gastos por categoría"""
    db = DatabaseManager()
    transacciones = db.leer_transacciones()
    
    if not transacciones:
        print("📊 No hay transacciones para analizar")
        return
    
    # Agrupar por categoría
    por_categoria = defaultdict(lambda: {'total': Decimal(0), 'cantidad': 0})
    
    for t in transacciones:
        if t.get('es_ingreso', 'False') == 'True':
            continue
        
        categoria = t.get('categoria') or 'Sin categoría'
        monto = Decimal(t['monto'])
        
        por_categoria[categoria]['total'] += monto
        por_categoria[categoria]['cantidad'] += 1
    
    # Ordenar por total
    ordenado = sorted(por_categoria.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print("\n💰 Gastos por Categoría:")
    print("="*70)
    print(f"{'Categoría':<20} {'Total':<15} {'Cantidad':<10} {'Promedio':<15}")
    print("-"*70)
    
    for categoria, datos in ordenado:
        promedio = datos['total'] / datos['cantidad']
        print(f"{categoria:<20} ${datos['total']:>12.2f} {datos['cantidad']:>8} ${promedio:>12.2f}")
    
    print("="*70)


def analizar_por_metodo_pago():
    """Analizar gastos por método de pago"""
    db = DatabaseManager()
    transacciones = db.leer_transacciones()
    
    if not transacciones:
        print("📊 No hay transacciones para analizar")
        return
    
    por_metodo = defaultdict(lambda: {'total': Decimal(0), 'cantidad': 0})
    
    for t in transacciones:
        if t.get('es_ingreso', 'False') == 'True':
            continue
        
        metodo = t.get('metodo_pago') or 'No especificado'
        monto = Decimal(t['monto'])
        
        por_metodo[metodo]['total'] += monto
        por_metodo[metodo]['cantidad'] += 1
    
    ordenado = sorted(por_metodo.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print("\n💳 Gastos por Método de Pago:")
    print("="*70)
    print(f"{'Método':<25} {'Total':<15} {'Cantidad':<10}")
    print("-"*70)
    
    for metodo, datos in ordenado:
        print(f"{metodo:<25} ${datos['total']:>12.2f} {datos['cantidad']:>8}")
    
    print("="*70)


def analizar_por_fuente():
    """Analizar gastos por fuente de dinero"""
    db = DatabaseManager()
    transacciones = db.leer_transacciones()
    
    if not transacciones:
        print("📊 No hay transacciones para analizar")
        return
    
    por_fuente = defaultdict(lambda: {'total': Decimal(0), 'cantidad': 0})
    
    for t in transacciones:
        if t.get('es_ingreso', 'False') == 'True':
            continue
        
        fuente = t.get('fuente_dinero') or 'No especificado'
        monto = Decimal(t['monto'])
        
        por_fuente[fuente]['total'] += monto
        por_fuente[fuente]['cantidad'] += 1
    
    ordenado = sorted(por_fuente.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print("\n🏦 Gastos por Fuente de Dinero:")
    print("="*70)
    print(f"{'Fuente':<30} {'Total':<15} {'Cantidad':<10}")
    print("-"*70)
    
    for fuente, datos in ordenado:
        print(f"{fuente:<30} ${datos['total']:>12.2f} {datos['cantidad']:>8}")
    
    print("="*70)


def analizar_fijos_vs_variables():
    """Analizar gastos fijos vs variables"""
    db = DatabaseManager()
    transacciones = db.leer_transacciones()
    
    if not transacciones:
        print("📊 No hay transacciones para analizar")
        return
    
    fijos = Decimal(0)
    variables = Decimal(0)
    sin_clasificar = Decimal(0)
    
    for t in transacciones:
        if t.get('es_ingreso', 'False') == 'True':
            continue
        
        monto = Decimal(t['monto'])
        tipo = t.get('tipo_gasto')
        
        if tipo == 'fijo':
            fijos += monto
        elif tipo == 'variable':
            variables += monto
        else:
            sin_clasificar += monto
    
    total = fijos + variables + sin_clasificar
    
    print("\n📊 Gastos Fijos vs Variables:")
    print("="*50)
    
    if total > 0:
        print(f"Gastos Fijos:        ${fijos:>12.2f}  ({fijos/total*100:>5.1f}%)")
        print(f"Gastos Variables:    ${variables:>12.2f}  ({variables/total*100:>5.1f}%)")
        print(f"Sin Clasificar:      ${sin_clasificar:>12.2f}  ({sin_clasificar/total*100:>5.1f}%)")
        print("-"*50)
        print(f"Total:               ${total:>12.2f}")
    else:
        print("No hay gastos registrados")
    
    print("="*50)


def resumen_completo():
    """Mostrar resumen completo"""
    db = DatabaseManager()
    stats = db.obtener_estadisticas()
    
    print("\n" + "="*70)
    print("📊 RESUMEN COMPLETO DE FINANZAS")
    print("="*70)
    
    if stats['total_transacciones'] == 0:
        print("No hay transacciones registradas")
        return
    
    print(f"\n💵 Balance General:")
    print(f"  Ingresos:     ${stats['total_ingresos']:>12.2f}")
    print(f"  Gastos:       ${stats['total_gastos']:>12.2f}")
    print(f"  Balance:      ${stats['balance']:>12.2f}")
    print(f"  Transacciones: {stats['total_transacciones']}")
    
    analizar_fijos_vs_variables()
    analizar_por_categoria()
    analizar_por_metodo_pago()
    analizar_por_fuente()
    
    print("\n" + "="*70)


def main():
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "categoria":
            analizar_por_categoria()
        elif comando == "metodo":
            analizar_por_metodo_pago()
        elif comando == "fuente":
            analizar_por_fuente()
        elif comando == "tipos":
            analizar_fijos_vs_variables()
        elif comando == "completo":
            resumen_completo()
        else:
            print(f"❌ Comando desconocido: {comando}")
            mostrar_ayuda()
    else:
        # Por defecto mostrar resumen completo
        resumen_completo()


def mostrar_ayuda():
    print("""
📊 Analizador de Finanzas

Uso: python analizar.py [comando]

Comandos:
  completo    Resumen completo (default)
  categoria   Gastos por categoría
  metodo      Gastos por método de pago
  fuente      Gastos por fuente de dinero
  tipos       Gastos fijos vs variables
""")


if __name__ == "__main__":
    main()
