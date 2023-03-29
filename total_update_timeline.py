import traceback
from datetime import date, timedelta, datetime
from mysql_realtime_update import mysql_updater, NoDataException, ZeroDataException
from carrier_maker import carrier_updater
import gc
import sys
import time

if __name__ == '__main__':
    clean0 = True ## 줄바꾸기를 위한 장치.  clean0=True 일 경우 '\r'을 통해 '마지막 수신' 이 같은 자리에 계속 표시되게 함. clean0이 False로 바뀔 때 \n 을 통해 \r 을 지움.
    while True:
        now0 = datetime.now()
        try:
            before_count, before_max, before_min, after_count, after_max, after_min, num_recieve, num_deal, num_doc2vec, num_deleted, num_corrected, clean0 = mysql_updater(clean0)
            if num_doc2vec !=0 or num_deleted != 0 or num_corrected !=0: #처리한게 하나라도 있으면.
                if clean0:
                    print('\n============')
                    clean0 = False
                print(f"마지막 업데이트 : {now0} // mysql : {before_count} -> {after_count} // api {num_recieve}개 받아 {num_doc2vec}개 전환// {num_deleted}개 삭제 {num_corrected}개 수정// {after_min} ~ {after_max}")
                print("============")
            else:  # 처리한 게 하나도 없을 경우.
                # clean0 =True
                # print(f"\r마지막 수신 : {now0}",end='')
                # print(f"마지막 수신 : {now0}",end='||')
                pass
        except NoDataException:
            pass
        except ZeroDataException:
            pass
        except:
            traceback.print_exc()

        ## carrier 업데이트
        try:
            carrier_updater()
        except:
            traceback.print_exc()
        time.sleep(120)

        sys.stdout.flush()
        gc.collect()

