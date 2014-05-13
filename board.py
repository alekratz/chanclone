from post import Post

class Board:
  def __init__(self, db, url, name, subtext):
    self.db = db
    self.url = url
    self.name = name
    self.subtext = subtext

  def getPosts():
    result = self.db.execute("select * from post where board='"+"'")
    entries = result.fetchall()
    posts = []
    for post in entries:
      newPost = Post(post['id'], post['post_time'], post['board'], post['title'],
        post['name'], post['content'], post['image_src'], post['parent'])
      posta.append(newPost)
    return posts
