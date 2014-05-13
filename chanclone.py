#!/usr/bin/python

import sqlite3, os, logging
from logging.handlers import RotatingFileHandler as RFH
from flask import Flask, render_template, g, request, flash
from werkzeug.routing import BaseConverter
from post import Post
from board import Board, getBoards, reloadBoardCache

# Load the application
app = Flask(__name__)
app.config.from_object(__name__)

class RegexConverter(BaseConverter):
  def __init__(self, url_map, *items):
    super(RegexConverter, self).__init__(url_map)
    self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter
# Load default config and override config from the environment
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, "chanclone.db"),
  DEBUG=True,
  SECRET_KEY='SECRET_DEVELOPMENT_KEY',
  USERNAME='admin',
  PASSWORD='changeme'
))

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
  if request.method == "POST":
    title = request.form['title']
    name = "Anonymous" if request.form["name"] == "" else request.form["name"]
    content = request.form["content"]
    parent = number
    db = get_db();
    db.execute(
    """
    insert into post(post_time, board, title, name, content, image_src, parent)
    values (datetime('now'), ?, ?, ?, ?, null, ?)
    """, [board, title, name, content, parent])
    db.commit();
    return "<center><h1>Post successful!</h1></center>"

@app.route("/<board>/newthread/", methods=['POST'])
def newthread(board):
  if request.method == "POST":
    title = request.form["title"]
    name = "Anonymous" if request.form["name"] == "" else request.form["name"]
    content = request.form["content"]
    db = get_db()
    db.execute(
      """
      insert into post(post_time, board, title, name, content, image_src)
      values (datetime('now'), ?, ?, ?, ?, null)
      """, [board, title, name, content])
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
