# functions/compraCripto.py
import uuid
from datetime import datetime
from flask import Flask, jsonify
from tinydb import TinyDB, Query
from filas.filaPedido import FilaPedidos

app = Flask(__name__)

# Inicializa banco de dados e fila
db_orders = TinyDB("db/orders.json")
db_crypto = TinyDB("db/cadastroCriptomoeda.json")
db_transactions = TinyDB("db/transactions.json")
fila = FilaPedidos()

Order = Query()
Crypto = Query()


def buscar_order(order_id: str):
    """
    Busca um pedido no banco de dados.
    """
    result = db_orders.search(Order.order_id == order_id)
    return result[0] if result else None


def buscar_crypto(crypto_id: str):
    """
    Busca uma criptomoeda no banco de dados.
    """
    result = db_crypto.search(Crypto.crypto_id == crypto_id)
    return result[0] if result else None


def atualizar_status(order_id: str, novo_status: str):
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


def atualizar_quantidade_crypto(crypto_id: str, nova_quantidade: float):
    """
    Atualiza a quantidade disponível de uma criptomoeda.
    """
    db_crypto.update(
        {
            "quantity": nova_quantidade,
            "updated_at": datetime.utcnow().isoformat()
        },
        Crypto.crypto_id == crypto_id
    )


def registrar_transacao(order_id: str, crypto_id: str, quantity: float, price_usd: float, user_id: str):
    """
    Registra a transação realizada.
    """
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "order_id": order_id,
        "crypto_id": crypto_id,
        "quantity": quantity,
        "price_usd": price_usd,
        "total_usd": quantity * price_usd,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    db_transactions.insert(transaction)
    return transaction


def processar_compra(order: dict, crypto: dict):
    """
    Processa a compra da criptomoeda.
    Valida regras de negócio e executa a transação.
    """
    quantity = order["quantity"]
    crypto_id = crypto["crypto_id"]
    
    # Validação 1: Criptomoeda está ativa?
    if crypto.get("status") != "active":
        raise Exception(f"Criptomoeda {crypto_id} não está disponível para compra")
    
    # Validação 2: Quantidade mínima
    min_order = crypto.get("min_order_size", 0)
    if quantity < min_order:
        raise Exception(f"Quantidade mínima para compra: {min_order}")
    
    # Validação 3: Quantidade máxima
    max_order = crypto.get("max_order_size", float('inf'))
    if quantity > max_order:
        raise Exception(f"Quantidade máxima para compra: {max_order}")
    
    # Validação 4: Estoque disponível
    available = crypto.get("quantity", 0)
    if quantity > available:
        raise Exception(f"Estoque insuficiente. Disponível: {available}")
    
    # Calcula valores
    price_usd = crypto["price_usd"]
    total_usd = quantity * price_usd
    
    # Atualiza estoque
    nova_quantidade = available - quantity
    atualizar_quantidade_crypto(crypto_id, nova_quantidade)
    
    # Registra transação
    transaction = registrar_transacao(
        order["order_id"],
        crypto_id,
        quantity,
        price_usd,
        order["user_id"]
    )
    
    # Atualiza status do pedido
    atualizar_status(order["order_id"], "concluído")
    
    return {
        "mensagem": "Compra processada com sucesso",
        "order_id": order["order_id"],
        "transaction": transaction,
        "resumo": {
            "crypto": crypto["symbol"],
            "quantidade": quantity,
            "preco_unitario": price_usd,
            "total_pago": total_usd,
            "estoque_restante": nova_quantidade
        }
    }


@app.route("/processar-compra", methods=["POST"])
def processar_proximo_da_fila():
    """
    Processa o próximo pedido da fila.
    """
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


@app.route("/processar-fila-completa", methods=["POST"])
def processar_fila_completa():
    """
    Processa todos os pedidos da fila (útil para testes).
    """
    resultados = []
    
    while True:
        item = fila.consumir()
        if not item:
            break
        
        order_id = item["pedido_id"]
        atualizar_status(order_id, "processando")
        
        order = buscar_order(order_id)
        crypto = buscar_crypto(order["crypto_id"]) if order else None
        
        try:
            if not order:
                resultado = {"order_id": order_id, "erro": "Pedido não encontrado"}
            elif not crypto:
                resultado = {"order_id": order_id, "erro": "Criptomoeda não encontrada"}
            else:
                resultado = processar_compra(order, crypto)
        except Exception as e:
            atualizar_status(order_id, "erro")
            resultado = {"order_id": order_id, "erro": str(e)}
        
        resultados.append(resultado)
    
    return jsonify({
        "total_processados": len(resultados),
        "resultados": resultados
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)