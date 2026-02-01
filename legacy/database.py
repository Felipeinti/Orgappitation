"""
Gestión de base de datos usando CSV
"""
import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from models import Transaccion, PrecioReferencia


class DatabaseManager:
    """Gestor de base de datos CSV"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.transacciones_file = self.data_dir / "transacciones.csv"
        self.precios_file = self.data_dir / "precios_referencia.csv"
        
        self._inicializar_archivos()
    
    def _inicializar_archivos(self):
        """Crear archivos CSV si no existen"""
        # Transacciones
        if not self.transacciones_file.exists():
            with open(self.transacciones_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_transaccion_fields())
                writer.writeheader()
        
        # Precios
        if not self.precios_file.exists():
            with open(self.precios_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_precio_fields())
                writer.writeheader()
    
    @staticmethod
    def _get_transaccion_fields() -> List[str]:
        """Campos del CSV de transacciones"""
        return [
            'id', 'fecha', 'monto', 'moneda', 'tipo_gasto', 'metodo_pago',
            'fuente_dinero', 'descripcion', 'categoria', 'notas', 'es_ingreso',
            'tasa_cambio', 'monto_convertido', 'moneda_convertida'
        ]
    
    @staticmethod
    def _get_precio_fields() -> List[str]:
        """Campos del CSV de precios"""
        return ['id', 'fecha', 'simbolo', 'precio', 'fuente', 'notas']
    
    def agregar_transaccion(self, transaccion: Transaccion) -> bool:
        """Agregar una transacción al CSV"""
        try:
            with open(self.transacciones_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_transaccion_fields())
                
                # Convertir el modelo a dict
                data = transaccion.model_dump()
                
                # Formatear fecha
                data['fecha'] = data['fecha'].isoformat()
                
                # Convertir enums a strings
                for key in ['tipo_gasto', 'metodo_pago', 'moneda', 'moneda_convertida']:
                    if data.get(key) is not None:
                        data[key] = str(data[key].value) if hasattr(data[key], 'value') else str(data[key])
                
                # Convertir Decimals a strings
                for key in ['monto', 'tasa_cambio', 'monto_convertido']:
                    if data.get(key) is not None:
                        data[key] = str(data[key])
                
                writer.writerow(data)
            return True
        except Exception as e:
            print(f"Error al agregar transacción: {e}")
            return False
    
    def agregar_precio_referencia(self, precio: PrecioReferencia) -> bool:
        """Agregar un precio de referencia al CSV"""
        try:
            with open(self.precios_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_precio_fields())
                
                data = precio.model_dump()
                data['fecha'] = data['fecha'].isoformat()
                data['precio'] = str(data['precio'])
                
                writer.writerow(data)
            return True
        except Exception as e:
            print(f"Error al agregar precio: {e}")
            return False
    
    def leer_transacciones(self, limite: Optional[int] = None) -> List[dict]:
        """Leer transacciones del CSV"""
        transacciones = []
        try:
            with open(self.transacciones_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transacciones.append(row)
                    if limite and len(transacciones) >= limite:
                        break
        except Exception as e:
            print(f"Error al leer transacciones: {e}")
        
        return transacciones
    
    def leer_precios(self, limite: Optional[int] = None) -> List[dict]:
        """Leer precios de referencia del CSV"""
        precios = []
        try:
            with open(self.precios_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    precios.append(row)
                    if limite and len(precios) >= limite:
                        break
        except Exception as e:
            print(f"Error al leer precios: {e}")
        
        return precios
    
    def obtener_estadisticas(self) -> dict:
        """Obtener estadísticas básicas"""
        transacciones = self.leer_transacciones()
        
        if not transacciones:
            return {"total_transacciones": 0}
        
        total = len(transacciones)
        total_gastos = sum(float(t['monto']) for t in transacciones if not t.get('es_ingreso', 'False') == 'True')
        total_ingresos = sum(float(t['monto']) for t in transacciones if t.get('es_ingreso', 'False') == 'True')
        
        return {
            "total_transacciones": total,
            "total_gastos": total_gastos,
            "total_ingresos": total_ingresos,
            "balance": total_ingresos - total_gastos
        }
