#!/usr/bin/python

import sqlite3, os, logging, time
from logging.handlers import RotatingFileHandler as RFH
from flask import Flask, render_template, g, request, flash, redirect, url_for, send_from_directory
from werkzeug.routing import BaseConverter
from werkzeug.utils import secure_filename
from post import Post
from board import Board, getBoards, reloadBoardCache
try:
  from PIL import Image, ImageOps
except ImportError:
  raise RuntimeError('Image module of PIL needs to be installed')

# Load the application
app = Flask(__name__)
app.config.from_object(__name__)

class RegexConverter(BaseConverter):
  def __init__(self, url_map, *items):
    super(RegexConverter, self).__init__(url_map)
    self.regex = items[0]

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'bmp', 'gif' ]

# Load default config and override config from the environment
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, "chanclone.db"),
  DEBUG=True,
  SECRET_KEY='SECRET_DEVELOPMENT_KEY',
  USERNAME='admin',
  PASSWORD='changeme',
  UPLOAD_FOLDER='static/img',
))

# Set up the regex converter to be used for regexes
app.url_map.converters['regex'] = RegexConverter

#
# Utility functions
#
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_file_ext(filename):
  if '.' in filename:
    return filename.rsplit(".", 1)[1]
  else:
    return ''

def verify_path(location, mkDir=True):
  if os.path.exists(location) and os.path.isdir(location):
    return True
  elif mkDir:
    os.makedirs(location, 0755)
    return True
  else:
    return False

def thumbnail(imgUrl, size="200x200"):
  width, height = [int(x) for x in size.split('x')]
  urlPath, imgName = os.path.split(imgUrl)
  # expecting this to be something like /img/g/1234.jpg or whatever
  thumbsPath = urlPath.replace('img', 'thumbs', 1)

  localPath = os.path.join("static", urlPath[1:], imgName) # discard leading slash
  localThumbsPath = os.path.join("static", thumbsPath[1:]) # discard leading slash

  verify_path(localPath, False)
  verify_path(localThumbsPath) # make the directory if it doesn't exist

  # server-side location
  thumbFilepath = os.path.join(localThumbsPath, imgName)
  if(os.path.exists(thumbFilepath)):
    # client-side url
    return os.path.join(thumbsPath, imgName)

  # create the file here
  else:
    try:
      image = Image.open(localPath)
    except IOError:
      return None

    img = image.copy()
    img.thumbnail((width, height), Image.ANTIALIAS)

    img.save(thumbFilepath, image.format, quality=85)
    return os.path.join(thumbsPath, imgName)
  
#
# Database methods
#
def connect_db():
  rv = sqlite3.connect(app.config['DATABASE'])
  rv.row_factory = sqlite3.Row
  return rv

def get_db():
  if not hasattr(g, 'sqlite_db'):
    g.sqlite_db = connect_db()
  return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
  if(hasattr(g, "sqlite_db")):
    g.sqlite_db.close()

def init_db():
  # continue if the file exists
  if os.path.isfile('chanclone.db'):
    return
  app.logger.debug("Creating new database")
  with app.app_context():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

#
# Routing methods
#

@app.route("/<regex('img|thumbs'):res>/<board>/<regex('[0-9]+\\.[a-zA-Z]+'):filename>")
def staticImage(res, board, filename):
  path = os.path.join("static", res, board)
  return send_from_directory(path, filename)

@app.route("/<board>/")
def boardPage(board):
  """
  Routes to the index page of a board. Prints a list of threads and the
  last few replies to that thread.
  """
  b = getBoards(get_db())[board]
  posts = b.getPosts(get_db())
  app.logger.info("Retrieving " + str(len(posts)) + " posts")
  return render_template("board.html", board=board,
    post_list=posts)

@app.route("/<board>/<regex('[0-9]+'):number>")
def resPage(board, number):
  """
  Gets the page of a thread for responses to that thread. Prints all of
  the responses.
  """
  b = getBoards(get_db())[board]
  post = b.getPosts(get_db())[int(number)]
  if post == None:
    return "<center><h1>404</h1></center>"
  else:
    return render_template("board.html", board=board,
      post_list={post.number : post}, number=number)

@app.route("/<board>/<regex('[0-9]+'):number>/res", methods=['POST'])
def respond(board, number):
  """
  The post page for after a response was made. Handles making the post
  and uploads the image if any.
  """
  title = request.form['title']
  name = "Anonymous" if request.form["name"] == "" else request.form["name"]
  content = request.form["content"]
  parent = number
  image_src = None

  upload = request.files['image']
  if upload:
    if allowed_file(upload.filename):
      filename = "{0}.{1}".format(int(time.time()), get_file_ext(upload.filename))
      upload_path = os.path.join(app.config['UPLOAD_FOLDER'], "img", board)
      verify_path(upload_path)
      upload.save(os.path.join(upload_path, filename))
      image_src = os.path.join("img", board, filename)
    else:
      return "<center><h1>Error: file must be an image</h1></center>"

  if image_src == None and content == "":
    return "<center><h1>You must fill out either the file or content form</h1></center>"

  db = get_db();
  db.execute(
  """
  insert into post(post_time, board, title, name, content, image_src, parent)
  values (datetime('now'), ?, ?, ?, ?, ?, ?)
  """, [board, title, name, content, image_src, parent])
  db.commit();
  return "<center><h1>Post successful!</h1></center>"

@app.route("/<board>/newthread/", methods=['POST'])
def newthread(board):
  """
  Handles creation of a new thread. Must include a file upload. May change later.
  """
  if request.method == "POST":
    title = request.form["title"]
    name = "Anonymous" if request.form["name"] == "" else request.form["name"]
    content = request.form["content"]
    image_src = None

    # Image uploading
    upload = request.files['image']
    if upload:
      if allowed_file(upload.filename):
        filename = "{0}.{1}".format(int(time.time()), get_file_ext(upload.filename))
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], board)
        verify_path(upload_path)
        upload.save(os.path.join(upload_path, filename))
        image_src = os.path.join("/", "img", board, filename)
      else:
        return "<center><h1>Error: file must be an image</h1></center>"

    if image_src == None:
      return "<center><h1>You must include an image to start a new thread</h1></center>"
    db = get_db()
    db.execute(
      """
      insert into post(post_time, board, title, name, content, image_src)
      values (datetime('now'), ?, ?, ?, ?, ?)
      """, [board, title, name, content, image_src])
    db.commit()
    app.logger.info("Added new post in " + board)
    return "<center><h1>Post successful!</h1></center"

@app.route("/")
def index():
  return "<h1>It works!</h1>"

if __name__ == "__main__":
  handler = RFH("chanclone.log", maxBytes=100 * 1024 * 1024)
  handler.setLevel(logging.INFO)
  app.logger.addHandler(handler)
  init_db()

  # add thumbnail function to the app
  app.jinja_env.filters['thumbnail'] = thumbnail

  app.run()
