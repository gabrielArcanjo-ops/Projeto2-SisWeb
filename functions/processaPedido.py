# functions/processaPedido.py
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from filas.filaPedido import FilaPedidos

app = Flask(__name__)

# Inicializa banco de dados e fila
db_orders = TinyDB("db/orders.json")
db_crypto = TinyDB("db/cadastroCriptomoeda.json")
fila = FilaPedidos()

Order = Query()
Crypto = Query()


def criar_order(crypto_id: str, quantity: float, user_id: str):
    """
    Cria um novo pedido no banco de dados.
    """
    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "crypto_id": crypto_id,
        "quantity": quantity,
        "user_id": user_id,
        "status": "criado",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    db_orders.insert(order)
    return order


def atualizar_status_order(order_id: str, novo_status: str):
    """
    Atualiza o status de um pedido.
    """
    db_orders.update(
        {
            "status": novo_status,
            "updated_at": datetime.utcnow().isoformat()
        },
        Order.order_id == order_id
    )


@app.route("/pedido", methods=["POST"])
def endpoint_criar_pedido():
    """
    POST /pedido
    {
      "crypto_id": "btc",
      "quantity": 0.1,
      "user_id": "usuario123" 
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"erro": "JSON inválido ou ausente"}), 400

    crypto_id = data.get("crypto_id")
    quantity = data.get("quantity")
    user_id = data.get("user_id")

    # validações básicas
    if not crypto_id:
        return jsonify({"erro": "campo 'crypto_id' é obrigatório"}), 400
    
    if not user_id:
        return jsonify({"erro": "campo 'user_id' é obrigatório"}), 400
    
    try:
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"erro": "campo 'quantity' deve ser número > 0"}), 400

    # cria pedido no DB
    order = criar_order(crypto_id, quantity, user_id)

    # adiciona na fila
    fila_item = fila.adicionar(order["order_id"])

    # atualiza status
    atualizar_status_order(order["order_id"], "enfileirado")

    response = {
        "mensagem": "Pedido recebido e enfileirado",
        "order_id": order["order_id"],
        "fila_item": fila_item
    }
    return jsonify(response), 201


@app.route("/pedido/<order_id>", methods=["GET"])
def consultar_pedido(order_id: str):
    """
    Consulta o status de um pedido.
    GET /pedido/{order_id}
    """
    order = db_orders.search(Order.order_id == order_id)
    
    if not order:
        return jsonify({"erro": "Pedido não encontrado"}), 404
    
    return jsonify(order[0]), 200


@app.route("/pedidos/usuario/<user_id>", methods=["GET"])
def listar_pedidos_usuario(user_id: str):
    """
    Lista todos os pedidos de um usuário.
    GET /pedidos/usuario/{user_id}
    """
    orders = db_orders.search(Order.user_id == user_id)
    return jsonify({"pedidos": orders}), 200


if __name__ == "__main__":
     app.run(debug=True, port=5000)