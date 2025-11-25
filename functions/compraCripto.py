import uuid
from datetime import datetime
from flask import Flask, jsonify
from tinydb import TinyDB, Query
from queue.filaPedido import FilaPedidos


@app.route("/processar-compra", methods=["POST"])
def processar_proximo_da_fila():
    item = fila.consumir()

    if not item:
        return jsonify({"mensagem": "Fila vazia"}), 200

    order_id = item["pedido_id"]
    atualizar_status(order_id, "processando")

    order = buscar_order(order_id)
    if not order:
        atualizar_status(order_id, "erro")
        return jsonify({"erro": "Pedido não encontrado no banco"}), 404

    crypto = buscar_crypto(order["crypto_id"])
    if not crypto:
        atualizar_status(order_id, "erro")
        return jsonify({"erro": "Criptomoeda não encontrada"}), 404

    try:
        resultado = processar_compra(order, crypto)
        return jsonify(resultado), 200

    except Exception as e:
        atualizar_status(order_id, "erro")
        return jsonify({"erro": str(e)}), 400

