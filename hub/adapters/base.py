from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Clase base para todos los adapters de brokers"""
    
    @abstractmethod
    async def connect(self):
        """Conectar al broker"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbols):
        """Suscribirse a símbolos"""
        pass
    
    @abstractmethod
    async def get_tick(self):
        """Obtener un tick de la cola"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Desconectar"""
        pass
