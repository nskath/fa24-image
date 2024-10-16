import requests
from flask import Flask, jsonify, render_template, request, send_file
import random
import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = Flask(__name__)



global votes
votes = 0
xdim = 1
ydim = 1
tilesize = 1
approval = False
voteToken = ""
rand_token = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=20))


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/addClient', methods=["PUT"])
def add_client():
    meta = {"author": "Navtej Kathuria", "url": os.getenv("curr_app"), "token": rand_token}

    connection = requests.put(os.getenv("test_canvas") + '/registerClient/navtejk2', json=meta)
    response = connection.json()

    global xdim, ydim, tilesize

    if connection.status_code == 200:
        xdim = response['xdim']
        ydim = response['ydim']
        tilesize = response['tilesize']
        return "Client Added", 200
    elif connection.status_code == 415:
        return "Client Already Registered", 415
    else:
        return "Error Adding Client", 500


@app.route('/addImage', methods=["PUT"])
def add_image():
    global xdim, ydim, tilesize
    width = xdim * tilesize
    height = ydim * tilesize

    image_file = request.files['image']
    if not image_file:
        return "No image provided", 400

    image_path = 'uploaded_image.png'
    image_file.save(image_path)

    my_img = Image.open(image_path)
    resized = my_img.resize((width, height))
    resized.save('file.png')

    with open('file.png', 'rb') as file:
        files = {'file': file}
        second_connection = requests.post(os.getenv("test_canvas") + '/registerImage/navtejk2', files=files)

    if second_connection.status_code == 500:
        return "Invalid Image Size", 500
    elif second_connection.status_code == 416:
        return "Client ID not registered", 416
    else:
        return "Image Added", 200


@app.route('/registered', methods=["PUT"])
def registered():
    from_server = request.get_json()

    if from_server['authToken'] != rand_token:
        return "Invalid Token", 401

    global xloc, yloc, voteToken, approval
    xloc = from_server['xloc']
    yloc = from_server['yloc']
    voteToken = from_server['voteToken']
    approval = from_server['approved']

    return "OK", 200


@app.route('/image', methods=["GET"])
def get_image():
    global approval

    if approval:
        return send_file('file.png', mimetype='image/png'), 200
    else:
        return "Image Not Approved", 404


@app.route('/tile', methods=["GET"])
def get_tile():
    global approval, xloc, yloc, tilesize

    if approval:
        whole_image = Image.open('file.png')
        x_pix = xloc * tilesize
        y_pix = yloc * tilesize
        measure = (x_pix, y_pix, x_pix + tilesize, y_pix + tilesize)

        curr_tile = whole_image.crop(measure)
        curr_tile.save('tile.png')

        return send_file('tile.png', mimetype='image/png'), 200
    else:
        return "Image Not Approved", 404


@app.route('/votes', methods=["GET"])
def get_votes():
    global votes
    return jsonify({"votes": votes}), 200


@app.route('/votes', methods=["PUT"])
def put_votes():
    from_votes = request.get_json()

    if from_votes['authToken'] != rand_token:
        return "Invalid Token", 401

    global votes
    votes = from_votes['votes']
    return "Votes Updated", 200


@app.route('/votingfor/<vote_x>/<vote_y>', methods=["PUT"])
def cast_vote(vote_x, vote_y):
    global voteToken

    vote_json = {'voteToken': voteToken, 'xloc': vote_x, 'yloc': vote_y}
    connection = requests.put(os.getenv("test_canvas") + '/vote/navtejk2', json=vote_json)

    if connection.status_code == 200:
        return "Voted", 200
    else:
        return "Voting Error", connection.status_code


@app.route('/update', methods=["PUT"])
def update_tile():
    from_update = request.get_json()

    if from_update['authToken'] != rand_token:
        return "Invalid Token", 401

    neighbors = from_update['neighbors']
    global votes
    curr_max = votes
    highest = ''

    for neighbor in neighbors:
        temp_json = requests.get(neighbor + '/votes').json()
        temp_votes = temp_json['votes']
        if temp_votes > curr_max:
            highest = neighbor
            curr_max = temp_votes

    if highest:
        new_image = requests.get(highest + '/image')
        with open('file.png', 'wb') as f:
            f.write(new_image.content)
        return "Tile Updated", 200
    else:
        return "No Update Required", 200


if __name__ == '__main__':
    app.run(port=5000)
