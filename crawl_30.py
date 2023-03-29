import requests
import json
from database import  config
import mysql.connector
from datetime import date, timedelta
import binascii
import re

def online_check(title0):
    tit0 = title0.replace(' ','')
    online_list = ['영감한스푼','양종구의100세시대건강법','이헌재의인생홈런','베스트닥터의베스트건강법','병을이겨내는사람들','허진석의톡톡스타트업','전승훈의아트로드']
    for obj in online_list:
        if obj in tit0:
            return True
    return False



today0 = date.today()
for i in range(1,51):
    db = mysql.connector.connect(**config)
    cursor = db.cursor()
    print(f"날짜:{i}")
    day0 = today0 - timedelta(days=i)
    url = f'https://openapi.donga.com/newsList?p={day0.strftime("%Y%m%d")}'
    temp = requests.get(url)
    articles = json.loads(temp.content)['data']
    n=0
    for ar in articles:



        content = ar["content"]
        title = ar['title']
        if len(content)>400 and '[부고]' not in title and '[인사]' not in title and '[단신]' not in title:
            if (online_check(title) and ar['ispublish'] =='1') or ('서영아의100세카페' in title.replace(' ','') and ar['ispublish'] =='0'):
                pass
            else:
                n+=1
                print(f"{i}   {n}")
                content0 =content
                content = re.sub(r'[^\s]+@[a-zA-Z.]+', ' ',  content)
                content = re.sub(r'[!?.][^.]*$', '.', content)
                title = ar['title'].replace('"','“')
                cursor.execute(
                    f"""
                    insert ignore into news_recommend.news_ago values(
                    "{ar['gid']}", "{ar['createtime']}","{title.replace(' ','')}", "{title}", b'{bin(int(binascii.hexlify(content.encode("utf-8")), 16))[2:]}', "{ar['url']}", "{ar['thumburl']}","{ar['source']}","{ar['cate_code']}",{len(content)}, NULL,NULL)
                    """
                )
    db.commit()
# db.commit()