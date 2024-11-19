from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    print(username);

    # Генерация уникального ключа
    key = str(uuid.uuid4()).replace('-', '')

    return jsonify({"key": key})

if __name__ == '__main__':
    app.run(debug=True)
