"""
Ejecutor de órdenes - envía órdenes a brokers
"""


class OrderExecutor:
    """Ejecuta órdenes reales en brokers"""
    
    def __init__(self):
        """Inicializa ejecutor"""
        pass
    
    async def execute(self, order):
        """Ejecuta una orden en el broker especificado"""
        pass
    
    async def execute_coinbase(self, order):
        """Ejecuta orden en Coinbase"""
        pass
    
    async def execute_schwab(self, order):
        """Ejecuta orden en Schwab"""
        pass
