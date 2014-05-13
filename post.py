class Post:
  def __init__(self, db, num, datetime, board, title, name, content, image_src, parent):
    self.db = db
    self.number = num
    self.datetime = datetime
    self.board = board
    self.title = title
    self.name = name
    self.content = content
    self.image_src = image_src
    self.parent = parent
