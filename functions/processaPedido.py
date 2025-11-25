# functions/processaPedido.py
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from queue.filaPedido import FilaPedidos


@app.route("/pedido", methods=["POST"])
def endpoint_criar_pedido():

    POST /pedido
    {
      crypto_id: "btc",
      quantity: 0.1,
      user_id: "usuario123" 
    }

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"erro": "JSON inválido ou ausente"}), 400

    crypto_id = data.get("crypto_id")
    quantity = data.get("quantity")
    user_id = data.get("user_id")

    # validações básicas
    if not crypto_id:
        return jsonify({"erro": "campo 'crypto_id' é obrigatório"}), 400
    try:
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"erro": "campo 'quantity' deve ser número > 0"}), 400

    # cria pedido no DB
    order = criar_order(crypto_id, quantity, user_id)

    fila_item = fila.adicionar(order["order_id"])

    atualizar_status_order(order["order_id"], "enfileirado")

    response = {
        "mensagem": "Pedido recebido e enfileirado",
        "order_id": order["order_id"],
        "fila_item": fila_item
    }
    return jsonify(response), 201
