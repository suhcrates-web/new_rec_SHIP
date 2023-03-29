from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from konlpy.tag import Okt
import mysql.connector
from database import config
import codecs
import numpy as np
import binascii
import json

db = mysql.connector.connect(**config)
cursor = db.cursor()

### db=0  (기사 gid:벡터  환경 만들기. 30일치 긁어와서.)
okt = Okt()
model = Doc2Vec.load('donga2000.model')

cursor.execute(
    """
    select gid, content from news_recommend.news_ago
    """
)


for gid, content in cursor.fetchall():
    konlpy0 = okt.pos(codecs.decode(content, 'utf-8'), norm=True, join=True)
    vector0 = model.infer_vector(konlpy0).astype('float32')
    print(gid)
    cursor.execute(
        f"""
        update news_recommend.news_ago set  konlpy =b'{bin(int(binascii.hexlify(str(json.dumps(konlpy0)).encode("utf-8")), 16))[2:]}', vec=%s where gid='{gid}'
        """, (vector0.tobytes(),)
    )
db.commit()

## top_inex 가 남음.   그건 'carrier' 채우면서.
