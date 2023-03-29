## db 와 테이블 만들기

from database import config
import mysql.connector


db = mysql.connector.connect(**config)
cursor = db.cursor()

cursor.execute(
    """
    create database if not exists news_recommend default character set 'utf8';
    """
)


cursor.execute(
    """
    drop table if exists news_recommend.news_ago;
    """
)

cursor.execute(
    """
    create table if not exists news_recommend.news_ago(
    gid varchar(10),
    createtime timestamp,
    unique_tit varchar(100),
    title varchar(100),
    content mediumblob,
    url varchar(100),
    thumburl varchar(100),
    source varchar(10),
    cate_code varchar(3),
    length int,
    vec mediumblob,
    konlpy mediumblob,
    primary key (gid, unique_tit)
    );
    """
)


cursor.execute(
    """
    drop table if exists news_recommend.carrier;
    """
)

cursor.execute(
    """
    create table if not exists news_recommend.carrier(
    id0 varchar(1),   
    mat mediumblob,
    gid mediumblob,
    title mediumblob,
    url mediumblob,
    thumburl mediumblob
    );
    """
)

cursor.execute(
    """
    insert into news_recommend.carrier values("1",NULL,NULL,NULL,NULL,NULL)
    """
)
db.commit()