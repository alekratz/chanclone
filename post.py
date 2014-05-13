class Post:
  def __init__(self, num, post_time, board, title, name, content, image_src, parent):
    self.number = num
    self.post_time = post_time
    self.board = board
    self.title = title
    self.name = name
    self.content = content
    self.image_src = image_src
    self.parent = parent
    self.children = {}
