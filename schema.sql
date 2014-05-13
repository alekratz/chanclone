drop table if exists post;
drop table if exists board;

--  Each post has:
--    a post number (not null)
--    a subject (title)
--    a poster name
--    content
--    image resource (nullable)
--    parent post

create table post (
  id integer primary key autoincrement,
  post_time datetime not null,
  board varchar(10) not null,
  title varchar(255),
  name varchar(255) default 'Anonymous',
  content varchar(10000),
  image_src varchar(100),
  parent integer,

  foreign key(parent) references post(id),
  foreign key(board) references board(url)
);

create table board (
  url varchar(10) not null primary key,
  name varchar(255),
  subtext varchar(255)
);

insert into board values("g", "Technology", "install gentoo");
insert into board values("n", "News", "Goings-on");
