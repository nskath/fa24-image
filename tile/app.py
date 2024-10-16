import requests
from flask import Flask, jsonify, render_template, request, send_file
import random
import os
import dotenv
from PIL import Image

global votes
votes = 0
servers = []
xdim = 1
ydim = 1
tilesize = 1
global rand_token
rand_token = ""
token_list = []
for i in range (20): 
  token_list.append(random.choice('abcdefghijklmnopqrstuvwxyz'))
  i = i + 1

rand_token = ''.join(token_list)

print(rand_token)

app = Flask(__name__)

@app.route('/')
def index():
  return render_template("index.html")


@app.route('/addClient', methods=["PUT"])
def Button_Add_Client():

  meta = {"author" : "Navtej Kathuria", "url" : os.getenv("curr_app"), "token" : rand_token}

  connection = requests.put(os.getenv("test_canvas") + '/registerClient/navtejk2', json = meta)

  response = connection.json()

  global xdim
  global ydim
  global tilesize
  global width
  global height

  if connection.status_code == 200:
    xdim = response['xdim']
    ydim = response['ydim']
    tilesize = response['tilesize']
    print(xdim)
    print(ydim)
    return "Client Added", 200
  else:
    if connection.status_code == 415: 
      print("Client Already Added"), 415
    else:
      raise Exception("Something went wrong with adding the thing to the thing")


  if connection.status_code == 200: 
    return "Client Added", 200

@app.route('/addImage', methods=["PUT"])
def Button_Add_Image():
  global xdim
  global ydim
  global tilesize
  global width
  global height
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
    second_connection = requests.post(os.getenv("test_canvas") + '/registerImage/navtejk2', files = files)

  if second_connection.status_code == 500:
    return "Image is Wrong Size", 500
  if second_connection.status_code == 416: 
    return "Client ID not registered", 416
  else:
    return "Image Added", 200
  


@app.route('/registered', methods=["PUT"])
def PUT_registered():

  from_server = request.get_json()

  if from_server['authToken'] != rand_token:
    return "Invalid Token", 401
  global xloc
  global yloc
  global voteToken
  global approval

  xloc = from_server['xloc']
  yloc = from_server['yloc']
  voteToken = from_server['voteToken']
  print("my xloc:" , xloc)
  print("my yloc:" , yloc)
  approval = from_server['approved']
  print("Image Approval:" , approval)

  return "OK, lol", 200

@app.route('/image', methods=["GET"])
def GET_image():
  global approval
  
  if approval == True: 
    return send_file('file.png', mimetype='image/png'), 200
  else:
    return "Image Currently Not Approved", 404

@app.route('/tile', methods=["GET"])
def GET_tile():
  global approval
  global xloc
  global yloc
  global tilesize

  if approval == True: 
    whole_image = Image.open('file.png')
    x_pix = xloc * tilesize
    y_pix = yloc * tilesize

    measure = (x_pix, y_pix, x_pix + tilesize, y_pix + tilesize)

    curr_tile = whole_image.crop(measure)

    curr_tile.save('tile.png')

    return send_file('tile.png', mimetype='image/png'), 200
  else:
    return "Image Not Currently Approved", 404

@app.route('/votes', methods=["GET"])
def GET_votes():
  global votes
  return jsonify({"votes": votes}), 200

@app.route('/votes', methods=["PUT"])
def PUT_votes():
  global rand_token
  global votes
  global old_server_seq
  global new_server_seq
  old_server_seq = -1
  new_server_seq = 0
  from_votes = request.get_json()

  if from_votes['authToken'] != rand_token: 
    return "Authentication Failed", 401
  else:
    new_server_seq = from_votes['seq']
    if int(new_server_seq) < int(old_server_seq):
      return "Conflict Error", 409
    else:
      old_server_seq = new_server_seq
      votes = from_votes['votes']
      return "Updates votes", 200

  
@app.route('/votingfor/<vote_x>/<vote_y>', methods=["PUT"])
def DO_voting(vote_x, vote_y):
  global voteToken
  # implement way to get x and y loc and send it in json
  vote_json = {'voteToken' : voteToken, 'xloc':vote_x, 'yloc': vote_y}
  connection = requests.put(os.getenv("test_canvas") + '/vote/navtejk2', json = vote_json)
  if connection.status_code == 200:
    return "Voted", 200
  else:
    return "Error", connection.status_code
  

@app.route('/update', methods=["PUT"])
def PUT_update():
  global votes
  global rand_token
  global neighbors
  temp_json = {}
  neighbors = []
  curr_max = votes
  highest = ''
  from_update = request.get_json()

  if from_update['authToken'] != rand_token: 
    return "Invalid Auth Token", 401
  else:
    neighbors = from_update['neighbors']
    for neighbor in neighbors: 
      temp_json = requests.get(neighbor + '/votes').json()
      temp_votes = temp_json['votes']
      if temp_votes > curr_max:
        highest = neighbor
        curr_max = temp_votes
    print("neighbor with max votes:", highest)
    print("their votes:" , curr_max)
    print("my votes:" , votes)
    if highest == '': 
      return "My Image Won", 200
    else: 
      print('here') 
      print(temp_votes)
      new_image = requests.get(highest + '/image')
      ret = new_image.content
      with open('file.png', 'wb') as f:
        f.write(ret)
      return "New Image Saved", 200
      

    
        



  


