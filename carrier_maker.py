#### db2 업데이트
import numpy as np
import mysql.connector
from database import config
import time
import sys
from datetime import datetime

def carrier_updater():
    db = mysql.connector.connect(**config)
    cursor = db.cursor()

    vectors = []
    gid_list = []
    title_list = []
    url_list = []
    thumburl_list = []
    ## 동아
    cursor.execute(
        f"""
        select gid, title, url, thumburl, vec from news_recommend.news_ago where source='동아일보' order by createtime desc limit 400;
        """
    )


    for i, (gid, title, url, thumburl, vec) in enumerate(cursor.fetchall()):
        vectors.append(np.frombuffer(vec,dtype='float32'))
        gid_list.append(gid)
        title_list.append(title)
        url_list.append(url)
        thumburl_list.append(thumburl)

    ## 다른 언론사
    cursor.execute(
        f"""
        select gid, title, url, thumburl, vec from news_recommend.news_ago where source!='동아일보' and source != '경제뉴스' order by createtime desc limit 500;
        """
    )

    for i, (gid, title, url, thumburl, vec) in enumerate(cursor.fetchall()):
        vectors.append(np.frombuffer(vec, dtype='float32'))
        gid_list.append(gid)
        title_list.append(title)
        url_list.append(url)
        thumburl_list.append(thumburl)

    mat_b = np.array(vectors, dtype='float32')
    default0 = np.random.rand(50)
    cursor.execute(
        """
        update news_recommend.carrier set mat=%s,  gid=%s, title=%s, url=%s, thumburl=%s, default0=%s where id0='1'
        """,(mat_b.tobytes(), np.array(gid_list).astype('U9').tobytes(), np.array(title_list).astype('U59').tobytes(), np.array(url_list).astype('U68').tobytes(), np.array(thumburl_list).astype('U65').tobytes(), default0.astype('float32'))
    )

    db.commit()

if __name__ == '__main__':
    n=0
    while True:
        n+=1
        now0 = datetime.now()
        carrier_updater()
        print('did')
        sys.stdout.flush()
        time.sleep(60*4)