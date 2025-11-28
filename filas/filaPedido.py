# filas/filaPedido.py

import os
from tinydb import TinyDB
from datetime import datetime

class FilaPedidos:
    def __init__(self):
        # Descobre o diretório raiz do projeto
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Cria o caminho completo para o arquivo da fila
        db_path = os.path.join(project_root, "filas", "filaPedidos.json")
        
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