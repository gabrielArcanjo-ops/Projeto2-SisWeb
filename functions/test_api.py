#!/usr/bin/env python3
"""
Script de testes para a API de corretagem de criptomoedas
"""
import requests
import json
import time

# URLs dos serviços
PEDIDO_URL = "http://localhost:5000"
COMPRA_URL = "http://localhost:5001"


def print_response(title, response):
    """Imprime uma resposta formatada"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_criar_pedido():
    """Testa a criação de um pedido"""
    print("\n🧪 TESTE 1: Criar Pedido de BTC")
    
    data = {
        "crypto_id": "btc",
        "quantity": 0.5,
        "user_id": "usuario123"
    }
    
    response = requests.post(f"{PEDIDO_URL}/pedido", json=data)
    print_response("Criação de Pedido", response)
    
    if response.status_code == 201:
        return response.json()["order_id"]
    return None


def test_consultar_pedido(order_id):
    """Testa a consulta de um pedido"""
    print(f"\n🧪 TESTE 2: Consultar Pedido {order_id}")
    
    response = requests.get(f"{PEDIDO_URL}/pedido/{order_id}")
    print_response("Consulta de Pedido", response)


def test_processar_compra():
    """Testa o processamento de uma compra"""
    print("\n🧪 TESTE 3: Processar Compra da Fila")
    
    response = requests.post(f"{COMPRA_URL}/processar-compra")
    print_response("Processamento de Compra", response)


def test_pedido_quantidade_minima():
    """Testa validação de quantidade mínima"""
    print("\n🧪 TESTE 4: Pedido com Quantidade Abaixo do Mínimo")
    
    data = {
        "crypto_id": "btc",
        "quantity": 0.00001,  # Mínimo é 0.0001
        "user_id": "usuario123"
    }
    
    response = requests.post(f"{PEDIDO_URL}/pedido", json=data)
    print_response("Pedido com Quantidade Mínima", response)
    
    # Processa para ver o erro
    if response.status_code == 201:
        time.sleep(0.5)
        response2 = requests.post(f"{COMPRA_URL}/processar-compra")
        print_response("Resultado do Processamento", response2)


def test_pedido_estoque_insuficiente():
    """Testa validação de estoque"""
    print("\n🧪 TESTE 5: Pedido com Estoque Insuficiente")
    
    data = {
        "crypto_id": "btc",
        "quantity": 150.0,  # Estoque disponível: 100
        "user_id": "usuario123"
    }
    
    response = requests.post(f"{PEDIDO_URL}/pedido", json=data)
    print_response("Pedido com Estoque Insuficiente", response)
    
    # Processa para ver o erro
    if response.status_code == 201:
        time.sleep(0.5)
        response2 = requests.post(f"{COMPRA_URL}/processar-compra")
        print_response("Resultado do Processamento", response2)


def test_multiplos_pedidos():
    """Testa criação e processamento de múltiplos pedidos"""
    print("\n🧪 TESTE 6: Múltiplos Pedidos")
    
    pedidos = [
        {"crypto_id": "btc", "quantity": 0.1, "user_id": "usuario1"},
        {"crypto_id": "eth", "quantity": 1.0, "user_id": "usuario2"},
        {"crypto_id": "usdt", "quantity": 100.0, "user_id": "usuario3"},
    ]
    
    order_ids = []
    
    for pedido in pedidos:
        response = requests.post(f"{PEDIDO_URL}/pedido", json=pedido)
        if response.status_code == 201:
            order_id = response.json()["order_id"]
            order_ids.append(order_id)
            print(f"✅ Pedido criado: {order_id} - {pedido['crypto_id']}")
    
    print(f"\n📦 Total de pedidos criados: {len(order_ids)}")
    
    # Processa todos
    print("\n🔄 Processando toda a fila...")
    time.sleep(1)
    response = requests.post(f"{COMPRA_URL}/processar-fila-completa")
    print_response("Processamento em Lote", response)


def test_listar_pedidos_usuario():
    """Testa listagem de pedidos de um usuário"""
    print("\n🧪 TESTE 7: Listar Pedidos do Usuário")
    
    response = requests.get(f"{PEDIDO_URL}/pedidos/usuario/usuario123")
    print_response("Pedidos do Usuário", response)


def main():
    """Executa todos os testes"""
    print("="*60)
    print("🚀 INICIANDO TESTES DA API DE CRIPTOMOEDAS")
    print("="*60)
    
    try:
        # Teste básico de criação e processamento
        order_id = test_criar_pedido()
        if order_id:
            time.sleep(0.5)
            test_consultar_pedido(order_id)
            time.sleep(0.5)
            test_processar_compra()
        
        time.sleep(1)
        
        # Testes de validação
        test_pedido_quantidade_minima()
        time.sleep(1)
        test_pedido_estoque_insuficiente()
        time.sleep(1)
        
        # Teste de múltiplos pedidos
        test_multiplos_pedidos()
        time.sleep(1)
        
        # Listagem de pedidos
        test_listar_pedidos_usuario()
        
        print("\n" + "="*60)
        print("✅ TESTES CONCLUÍDOS")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar aos serviços.")
        print("Certifique-se de que os serviços estão rodando:")
        print("  - processaPedido.py na porta 5000")
        print("  - compraCripto.py na porta 5001")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")


if __name__ == "__main__":
    main()