####
# v1 : db 0 업데이트 작업
# 10초에 한번 api로 받아와, doc2vec 에 넣은 뒤  벡터 산출해 저장.
# api 정보는 mysql 에도 동시에 저장.

#v2 : online_checker 반영.
import requests
import json
import mysql.connector
from database import config
from datetime import date, timedelta, datetime
import binascii
import re
from gensim.models.doc2vec import Doc2Vec
from konlpy.tag import Okt
import numpy as np

class NoDataException(Exception):
    pass
class ZeroDataException(Exception):
    pass
def online_check(title0):
    tit0 = title0.replace(' ','')
    online_list = ['영감한스푼','양종구의100세시대건강법','이헌재의인생홈런','베스트닥터의베스트건강법','병을이겨내는사람들','허진석의톡톡스타트업','전승훈의아트로드']
    for obj in online_list:
        if obj in tit0:
            return True
    return False

def mysql_updater(clean0):
    okt = Okt()  # 형태소 변환 모듈

    today0 = date.today()

    articles = []
    api_dic = {}
    for n in range(2):  # 수정, 삭제는 이틀치를 확인해야 하기떄문에 이틀치 긁어옴.
        day0 = today0 - timedelta(days=n)  # 어제(n=1), 오늘(n=0)
        url = f'https://openapi.donga.com/newsList?p={day0.strftime("%Y%m%d")}'
        temp = requests.get(url)
        temp = json.loads(temp.content)
        if 'data' not in [*temp]:
            # 그냥 가끔 data 없이 올 떄가 있음. 그리고 새벽에 첫 기사 나오기 전까지는 'data'가 없음.
            print('### NoDataException ###')
            raise NoDataException()
        articles += temp['data']
    for ar in articles:
        # api_dic[ar['gid']] = ar['title']   ### 제목 수정 에서 쓸  딕셔너리.
        api_dic[ar['gid']] ={'title':ar['title'], 'thumburl':ar['thumburl']}

    if len([*api_dic]) ==0:
        print('### ZeroDataException ###')
        raise ZeroDataException

    ## 1) 새로 업데이트된 기사 정보를 mysql에 쌓음. 또 본문을 word2vec 으로 vec 변환해 redis에  'gid : vec' 형태로 저장함.

    db = mysql.connector.connect(**config)
    cursor = db.cursor()

    # 작업을 수행하기 전 상태 체크
    cursor.execute("""
    select gid from news_recommend.news_ago
    """)
    keys = np.array(cursor.fetchall()).reshape(1,-1)[0]
    before_count = len(keys)
    num_recieve = len(articles)  # api로 받은 숫자
    num_deal = 0  # 실제 처리대상 숫자..  400자 이상,  부고 인사 단신 제외
    num_doc2vec = 0  # doc2vec 처리돼 redis와 mysql에 들어간 숫자.
    write_ars = [] # 등록할 기사 목록
    for ar in articles:
        gid = ar['gid']
        if gid not in keys:  ## api에서 받은 게 mysql 에 없다면
            content = ar["content"]
            if len(content) > 400: #글자수 400 이상
                title = ar['title'].replace('"', '“')
                if '[부고]' not in title and '[인사]' not in title and '[단신]' not in title:

                    if (online_check(title) and ar['ispublish'] == '1') or (
                            '서영아의100세카페' in title.replace(' ', '') and ar['ispublish'] == '0'):
                        pass
                    else:
                        write_ars.append(ar)  # 작성대상 리스트에 쌓음.

    if len(write_ars) > 0:
        model = Doc2Vec.load('donga2000.model')  # doc2vec 모델 로드.
        for ar in write_ars:
                    num_deal += 1
                    title = ar['title'].replace('"', '“')
                    num_doc2vec +=1
                    if clean0:
                        print('\n============')
                        clean0 = False
                    print(f"기사 등록 : {ar['gid']} / {title} / {ar['url']}")
                    content = re.sub(r'\.com$','', ar['content'].strip())
                    temp = re.split(r'\.(?=[^.]*$)', content)
                    if len(temp) >1:
                        content, press = temp
                    else:
                        content, press = temp[0], 'unknown'

                    # doc2vec 변환 후 redis에 넣기
                    konlpy0 = okt.pos(content, norm=True, join=True)
                    vector0 = model.infer_vector(konlpy0).astype('float32')
                    # mysql에 넣기
                    cursor.execute(
                        f"""
                        insert ignore into news_recommend.news_ago values(
                        "{ar['gid']}", "{ar['createtime']}", "{title.replace(' ','')}", "{title}", b'{bin(int(binascii.hexlify(content.encode("utf-8")), 16))[2:]}', "{ar['url']}", "{ar['thumburl']}", "{ar['source']}","{ar['cate_code']}",{len(content)},%s, b'{bin(int(binascii.hexlify(str( json.dumps(konlpy0)).encode("utf-8")), 16))[2:]}'  )
                        """, (vector0.tobytes(),)
                    )
                      # 벡터를 mysql에도 저장. 인출떄는  np.array(json.loads(cursor.fetchall()[0][0]))
        db.commit()

    # 2) 기사 수정 및 삭제

    cursor.execute(
        f"""
        select gid, title, createtime, thumburl from news_recommend.news_ago where createtime >="{today0 - timedelta(days=1)}" and createtime < "{today0 + timedelta(days=1)}" 
        """
    )
    mysql_dic = {g: (t, c, th) for g, t, c, th in cursor.fetchall()}  # gid : title

    ### mysql 에 있는 것 중 api 에 없는것을 찾아야 함
    del_gid = []
    # correct_dic = {}  # gid : 바꿀제목
    correct_title = {}
    correct_thumburl = {}
    for gid in mysql_dic:
        # print(mysql_dic[gid][1], end=' ')
        if gid not in [*api_dic]:  ## mysql에 있는 gid가 api에는 없는경우  ==> 삭제
            #삭제할거
            if clean0:
                print('\n============')
                clean0 = False
            del_gid.append(gid)
            print(f"삭제 : {gid} / {mysql_dic[gid][0]}")

        elif api_dic[gid]['title'] != mysql_dic[gid][0]:  # gid가 있긴 한데 title이 다를 경우 ==> 수정
            if clean0:
                print('\n============')
                clean0 = False
            print(f"제목 수정 : {gid} / {mysql_dic[gid][0]} => {api_dic[gid]['title']}  ")
            correct_title[gid] = api_dic[gid]['title']

        elif api_dic[gid]['thumburl'] != mysql_dic[gid][2]:  # gid가 있긴 한데 title이 다를 경우 ==> 수정
            if clean0:
                print('\n============')
                clean0 = False
            print(f"썸네일url 수정 : {gid} / {mysql_dic[gid][2]} => {api_dic[gid]['thumburl']}  ")
            correct_thumburl[gid] = api_dic[gid]['thumburl']
            
        else:
            # print("이상없음")
            pass

    num_deleted = len(del_gid) # 삭제 수
    num_corrected = len(*[correct_title]) + len(*[correct_thumburl]) # 수정 수
    ## 삭제  실행
    if len(del_gid) >0:
        cursor.execute(
            f"""
                delete from news_recommend.news_ago where gid in ({','.join(del_gid)})
                """
        )


    ## 수정 실행
    sql = """update news_recommend.news_ago set title=%s where gid=%s"""
    cursor.executemany(sql, [(value, key) for key, value in correct_title.items()])
    db.commit()

    sql = """update news_recommend.news_ago set thumburl=%s where gid=%s"""
    cursor.executemany(sql, [(value, key) for key, value in correct_thumburl.items()])
    db.commit()

    ## 활동 정리
    cursor.execute("""
    select count(*), max(createtime), min(createtime) from news_recommend.news_ago
    """)
    after_count, after_max, after_min = cursor.fetchone()

    return before_count, after_count, after_max, after_min, num_recieve, num_deal, num_doc2vec, num_deleted, num_corrected, clean0

if __name__ == '__main__':
    import time
    import gc
    import sys

    clean0 = True ## 줄바꾸기를 위한 장치.  clean0=True 일 경우 '\r'을 통해 '마지막 수신' 이 같은 자리에 계속 표시되게 함. clean0이 False로 바뀔 때 \n 을 통해 \r 을 지움.
    while True:
        now0 = datetime.now()
        try:
            before_count, after_count, after_max, after_min, num_recieve, num_deal, num_doc2vec, num_deleted, num_corrected, clean0 = mysql_updater(clean0)
            if num_doc2vec !=0 or num_deleted != 0 or num_corrected !=0: #처리한게 하나라도 있으면.
                if clean0:
                    print('\n============')
                    clean0 = False
                print(f"마지막 업데이트 : {now0} // mysql : {before_count} -> {after_count} // api {num_recieve}개 받아 {num_doc2vec}개 전환// {num_deleted}개 삭제 {num_corrected}개 수정// {after_min} ~ {after_max}")
                print("============")
            else:  # 처리한 게 하나도 없을 경우.
                clean0 =True
                # print(f"\r마지막 수신 : {now0}",end='')
                print(f"마지막 수신 : {now0}",end='||')

        except NoDataException:
            pass
        except ZeroDataException:
            pass
        time.sleep(120)

        sys.stdout.flush()
        gc.collect()

