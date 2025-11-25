# queue/filaPedido.py

from tinydb import TinyDB
from datetime import datetime

class FilaPedidos:
    def __init__(self, db_path="queue/filaPedidos.json"):
        self.db = TinyDB(db_path)
        self.fila = self.db.table("fila")

    def adicionar(self, pedido_id: str):
        """
        Adiciona o ID do pedido na fila.
        """
        item = {
            "pedido_id": pedido_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.fila.insert(item)
        return item

    def consumir(self):
        """
        Remove e retorna o primeiro pedido da fila (FIFO).
        """
        dados = self.fila.all()
        
        if not dados:
            return None
        
        primeiro = dados[0]
        self.fila.remove(doc_ids=[primeiro.doc_id])
        return primeiro

    def listar(self):
        """
        Retorna todos os pedidos na fila (para debug).
        """
        return self.fila.all()
