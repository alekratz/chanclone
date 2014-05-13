from post import Post

# a global variable
board_cache = None

def reloadBoardCache():
  board_cache = None

def getBoards(db):
  global board_cache
  if board_cache == None:  
    result = db.execute("select * from board")
    entries = result.fetchall()
    print "entries:", len(entries)
    boards = {}
    for row in entries:
      b = Board(row['url'], row['name'], row['subtext'])
      boards[row['url']] = b
    board_cache = boards
  return board_cache

class Board:
  def __init__(self, url, name, subtext):
    self.url = url
    self.name = name
    self.subtext = subtext

  def getPosts(self, db):
    result = db.execute("select * from post where board=? order by post_time desc", self.url)
    entries = result.fetchall()
    posts = []
    for post in entries:
      newPost = Post(post['id'], post['post_time'], post['board'], post['title'],
        post['name'], post['content'], post['image_src'], post['parent'])
      posts.append(newPost)
    return posts

