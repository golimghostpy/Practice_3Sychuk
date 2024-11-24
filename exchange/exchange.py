from flask import Flask, request, jsonify
import uuid
import socket
import json
from ctypes import memset

app = Flask(__name__)
clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_to_server(message):
    try:
        clientSock.sendall(message.encode())
        response = clientSock.recv(1024)
        return response.decode()
    except Exception as e:
        print(f"Error communicating with server: {e}")

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')

    takenUsernames = send_to_server(f"SELECT user.username FROM user WHERE user.username = '{username}'").split("\n")[1:-2]
    if len(takenUsernames) != 0:
        return jsonify({"error": "Username is already exists"})

    while True:
        # Генерация уникального ключа
        key = str(uuid.uuid4()).replace('-', '')
        keyCheck = send_to_server(f"SELECT user.key FROM user WHERE user.key = '{key}'").split("\n")[1:-2]
        if len(keyCheck) == 0:
            break

    send_to_server(f"INSERT INTO user VALUES ('{username}', '{key}')")
    return jsonify({"key": key})

@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    userKey = request.headers.get('X-USER-KEY')

    if not userKey:
        return jsonify({"error": "You must enter your key"}), 400

    userId, keyCheck = send_to_server(f"SELECT user.user_id, user.key FROM user WHERE user.key = '{userKey}'").split("\n")[1].split(';')[:-1]
    if len(keyCheck) == 0:
        return jsonify({"error": "No such a key"}), 400

    if 'pair_id' not in data or 'quantity' not in data or 'price' not in data or 'type' not in data:
        return jsonify({"error": "Must enter fields: pair_id, quantity, price and type"}), 400

    # Отправляем сообщение на сервер
    response = send_to_server(f"INSERT INTO order VALUES ('{userId}', '{data['pair_id']}', '{data['quantity']}', '{data['price']}', '{data['type']}', '-')")

    with open('../bin/trader/order/order_pk_sequence.txt', 'r') as pkFile:
        orderId = int(pkFile.readline().strip()) - 1

    return jsonify({"order_id": orderId})

@app.route('/order', methods=['GET'])
def get_order():
    orders = send_to_server(f"SELECT order.order_id, order.user_id, order.pair_id, order.quantity, order.type, order.price, order.closed FROM order")

    response = []
    for order in orders.split("\n")[1:-2]:
        parts = order.split(";")
        response.append({"order_id": int(parts[0]), "user_id": int(parts[1]), "pair_id": int(parts[2]),
                         "quantity": float(parts[3]), "type": parts[4], "price": float(parts[5]), "closed": parts[6]})

    return jsonify(response)

@app.route('/order', methods=['DELETE'])
def delete_order():
    data = request.get_json()
    userKey = request.headers.get('X-USER-KEY')

    if not userKey:
        return jsonify({"error": "You must enter your key"}), 400

    userId, keyCheck = send_to_server(f"SELECT user.user_id, user.key FROM user WHERE user.key = '{userKey}'").split("\n")[1].split(';')[:-1]
    if len(keyCheck) == 0:
        return jsonify({"error": "No such a key"}), 400

    if 'order_id' not in data:
        return jsonify({'error': 'You must enter order_id to delete'}), 400

    try:
        orderOwner = send_to_server(f"SELECT order.user_id FROM order WHERE order.order_id = '{data['order_id']}'").split("\n")[1]
    except Exception:
        return jsonify({'error': 'No order with that id'}), 400

    if userId != orderOwner[:-1]:
        return jsonify({'error': 'It is not your order'}), 400

    send_to_server(f"DELETE FROM order WHERE order.order_id = '{data['order_id']}'")
    return jsonify({"message": "Order deleted successfully"}), 200

@app.route('/lot', methods=['GET'])
def get_lot():
    lots = send_to_server(f"SELECT lot.lot_id, lot.name FROM lot")

    response = []
    for order in lots.split("\n")[1:-2]:
        parts = order.split(";")
        response.append({"lot_id": int(parts[0]), "name": parts[1]})

    return jsonify(response)

@app.route('/pair', methods=['GET'])
def get_pair():
    pairs = send_to_server(f"SELECT pair.pair_id, pair.first_lot_id, pair.second_lot_id FROM pair")

    response = []
    for order in pairs.split("\n")[1:-2]:
        parts = order.split(";")
        response.append({"pair_id": int(parts[0]), "sale_lot_id": int(parts[1]), "buy_lot_id": int(parts[2])})

    return jsonify(response)

@app.route('/balance', methods=['GET'])
def get_balance():
    data = request.get_json()
    userKey = request.headers.get('X-USER-KEY')

    if not userKey:
        return jsonify({"error": "You must enter your key"}), 400

    userId, keyCheck = send_to_server(f"SELECT user.user_id, user.key FROM user WHERE user.key = '{userKey}'").split("\n")[1].split(';')[:-1]
    if len(keyCheck) == 0:
        return jsonify({"error": "No such a key"}), 400

    userLots = send_to_server(f"SELECT user_lot.lot_id, user_lot.quantity FROM user_lot WHERE user_lot.user_id = '{userId}'").split('\n')[1:-2]
    response = []
    for lot in userLots:
        parts = lot.split(';')
        response.append({'lot_id': parts[0], 'quantity': parts[1]})

    return jsonify(response)

def get_config():
    with open('config.json', 'r') as configFile:
        config = json.load(configFile)
        return [config['lots'], config['database_ip'], config['database_port']]

if __name__ == '__main__':
    lots, dbIP, dbPort = get_config()

    serverAddr = (str(dbIP), int(dbPort))
    clientSock.connect(serverAddr)

    app.run(debug=True)

