#!/usr/bin/python

import sqlite3, os
from flask import Flask, render_template, g
from post import Post
from board import Board, getBoards, reloadBoardCache

# Load the application
app = Flask(__name__)
app.config.from_object(__name__)

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
  return render_template("board.html", board=board,
    post_list=b.getPosts(get_db()))

@app.route("/<board>/newthread")
def newthread(board, method=['GET', 'POST']):
  if request.method == "POST":
    title = request.form["title"]
    name = "Anonymous" if request.form["name"] == "" else request.form["name"]
    content = request.form["content"]
    parent = 0

@app.route("/")
def index():
  return "<h1>It works!</h1>"

if __name__ == "__main__":
  init_db()
  app.run()
