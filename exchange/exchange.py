from flask import Flask, request, jsonify
import uuid
import socket
import json

app = Flask(__name__)

def send_to_server(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSock:
        try:
            clientSock.connect(serverAddr)
            clientSock.sendall(message.encode())
            response = clientSock.recv(1024)
            print('Message from server: ', response.decode())
        except Exception as e:
            print(f"Error communicating with server: {e}")

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')

    send_to_server(f"SELECT user.username, user.key FROM user WHERE user.username = '{username}'")

    # Генерация уникального ключа
    key = str(uuid.uuid4()).replace('-', '')

    #send_to_server(f"INSERT INTO user VALUES ('{username}', '{key}')")

    return jsonify({"key": key})

def get_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        return [config['lots'], config['database_ip'], config['database_port']]

if __name__ == '__main__':
    lots, dbIP, dbPort = get_config()

    serverAddr = (str(dbIP), int(dbPort))

    app.run(debug=True)

