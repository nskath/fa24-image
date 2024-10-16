from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

registered_clients = []
votes = {}

@app.route('/')
def index():
    return render_template('middleware_status.html')

@app.route('/auth', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    token = data.get('token')
    if validate_token(token):
        return jsonify({'message': 'Authentication successful'}), 200
    else:
        return jsonify({'error': 'Invalid token'}), 401

def validate_token(token):
    return token == 'correct-token'

@app.route('/registerClient', methods=['PUT'])
def register_client():
    data = request.get_json()
    client = {
        'clientID': data.get('clientID'),
        'url': data.get('url'),
        'author': data.get('author')
    }
    registered_clients.append(client)
    print(registered_clients)
    return jsonify({'message': 'Client registered'}), 200

@app.route('/registeredClients', methods=['GET'])
def view_registered_clients():
    return jsonify({'clients': registered_clients}), 200

@app.route('/vote/<clientID>', methods=['PUT'])
def cast_vote(clientID):
    data = request.get_json()
    vote_count = votes.get(clientID, 0) + 1
    votes[clientID] = vote_count
    return jsonify({'votes': vote_count}), 200

@app.route('/voteStatus/<clientID>', methods=['GET'])
def check_vote_status(clientID):
    if clientID not in votes:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify({'votes': votes[clientID]}), 200

if __name__ == '__main__':
    app.run(port=34000)
