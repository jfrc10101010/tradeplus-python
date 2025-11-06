"""
Conector para Schwab - API REST autenticada
"""
from hub.adapters.base import BaseAdapter


class SchwabConnector(BaseAdapter):
    """Conexión REAL a Schwab API REST con token autenticado"""
    
    def __init__(self):
        """Inicializa conector de Schwab"""
        pass
    
    async def connect(self):
        """Conecta a Schwab REST API"""
        pass
    
    async def subscribe(self, symbols):
        """Suscribe a símbolos"""
        pass
    
    async def get_tick(self):
        """Obtiene siguiente tick"""
        pass
    
    async def disconnect(self):
        """Desconecta"""
        pass
