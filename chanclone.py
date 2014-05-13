#!/usr/bin/python

import sqlite3, os
from flask import Flask, render_template, g
from post import Post

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

#
# Routing methods
#
@app.route("/<board>/")
def boardPage(board):
  return render_template("board.html", board=board,
    post_list=[Post(get_db(), 12, None, "g", "Welcome to /g/!", "Alek",
    """
    I'm just using this post to let you know that I welcome you to /g/!
    """, None, 0)])

@app.route("/")
def index():
  return "<h1>It works!</h1>"

if __name__ == "__main__":
  init_db()
  app.run()
