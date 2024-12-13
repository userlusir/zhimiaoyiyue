import json
import random
import time

import captcha
import customex
import networks

worker = None


def init(_worker):
    global worker
    worker = _worker


def crawler(mxid):
    global worker
    mxid = mxid.strip()
    while True:
        try:
            resp = worker.try_get(f"act=GetCaptcha&mxid={mxid}", handle_status=408)
            degree = int(captcha.solve(resp))
            resp = worker.try_get(f"act=CaptchaVerify&token=&x={degree}&y=5", handle_status=408)
            print("captcha solved.")
        except customex.MatchNotFoundError:
            print("new unsolved captcha.")
        except customex.StatusError:
            worker = networks.try_get_worker(interval=3)
        finally:
            time.sleep(3)


def scan_mxid(choose_one=False):
    month = time.strftime("%Y%m", time.localtime())
    resp = worker.try_get(f"act=GetCustSubscribeDateAll&pid={worker.vaccine_id}&id={worker.site_id}&month={month}")
    dates = [elem['date'] for elem in resp['list']]
    if choose_one:
        date = random.choice(dates)
        resp = worker.try_get(f"act=GetCustSubscribeDateDetail&pid={worker.vaccine_id}&id={worker.site_id}&scdate={date}")
        return random.choice(resp['list'])['mxid']
    else:
        for date in dates:
            time.sleep(1)
            resp = worker.try_get(f"act=GetCustSubscribeDateDetail&pid={worker.vaccine_id}&id={worker.site_id}&scdate={date}")
            print(f"{date}:{[elem['mxid'] for elem in resp['list']]}")
