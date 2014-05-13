#!/usr/bin/python

import sqlite3, os, logging, time
from logging.handlers import RotatingFileHandler as RFH
from flask import Flask, render_template, g, request, flash, redirect, url_for, send_from_directory
from werkzeug.routing import BaseConverter
from werkzeug.utils import secure_filename
from post import Post
from board import Board, getBoards, reloadBoardCache

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
  UPLOAD_FOLDER='static/img'
))

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

def verify_path(location):
  if os.path.exists(location) and os.path.isdir(location):
    return
  else:
    os.mkdir(location)

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
@app.route("/<board>/")
def boardPage(board):
  b = getBoards(get_db())[board]
  posts = b.getPosts(get_db())
  app.logger.info("Retrieving " + str(len(posts)) + " posts")
  return render_template("board.html", board=board,
    post_list=posts)

@app.route("/<board>/<regex('[0-9]+'):number>")
def resPage(board, number):
  b = getBoards(get_db())[board]
  post = b.getPosts(get_db())[int(number)]
  if post == None:
    return "<center><h1>404</h1></center>"
  else:
    return render_template("board.html", board=board,
      post_list={post.number : post}, number=number)

@app.route("/<board>/<regex('[0-9]+'):number>/res", methods=['POST'])
def respond(board, number):
  title = request.form['title']
  name = "Anonymous" if request.form["name"] == "" else request.form["name"]
  content = request.form["content"]
  parent = number
  image_src = None

  upload = request.files['image']
  if upload:
    if allowed_file(upload.filename):
      filename = "{0}.{1}".format(int(time.time()), get_file_ext(upload.filename))
      upload_path = os.path.join(app.config['UPLOAD_FOLDER'], board)
      verify_path(upload_path)
      upload.save(os.path.join(upload_path, filename))
      image_src = os.path.join(upload_path, filename)
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
        image_src = os.path.join(upload_path, filename)
      else:
        return "<center><h1>Error: file must be an image</h1></center>"

    if image_src == None and content == "":
      return "<center><h1>You must fill out either the file or content form</h1></center>"
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
  app.run()
