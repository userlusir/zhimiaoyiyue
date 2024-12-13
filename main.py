import datetime
import json
import os
import random
import re
import sys
import time

import crawler
import customex
import networks

import captcha

acc_info = []
dates = []
code_list = []

def main():
    captcha.init("./match")
    #sys.argv = [sys.argv[0], "-crawler"]
    with open("date.txt", "r", encoding="utf-8") as f:
        dates = eval(f.read())
        if dates is not None:
            dates = dates
            random.shuffle(dates)
        else:
            watch_date()
    running_mode = 0
    if len(sys.argv) > 1:
        if sys.argv[1] == "-crawler":
            running_mode = 1
            print("-crawler:爬虫模式启动")
    worker = networks.get_worker()
    pid_print("Successfully inited info files.")

    print("输入wait_seconds:")
    wait_seconds = float(input())

    print("输入site_id:")
    site_id = int(input())
    print("输入vaccine_text:")
    vaccine_text = str(input())
    print("输入针次：")
    ftime = int(input())

    print("输入code:")
    code_list = []
    end = ''
    for line in iter(input, end):
        code_list.append(line)
    worker.code_list = code_list
    worker.get_persson_info()

    print("输入sign:")
    sign = str(input())[0:16].encode('utf-8')
    worker.AES_key = sign

    worker.site_id = site_id
    worker.vaccine_text = vaccine_text
    worker.ftime = ftime
    _, vaccines = worker.query_site_info()
    for vaccine in vaccines:
        print(vaccine)
    if running_mode == 0:
        for vaccine in vaccines:
            if vaccine[0] == vaccine_text:
                print(vaccine[1])
                target_time = re.search(r"(\S+ \S+) *至 *(\S+ \S+)", vaccine[1]).group(1)
                target_time = f"{time.strftime('%Y', time.localtime())}-{target_time}:00"
                break
        else:
            raise Exception("Wrong vaccine id!")
        worker.ftime = ftime
        verify_info(worker)
        wait_time(wait_seconds, target_time)
        #watch_vaccine(worker)
        #dates = worker.submit_month()
        #worker.lines()
        #worker.get_vaccine_id()
        dates = worker.get_dates()
        worker.auto_reserve(dates)
    elif running_mode == 1:
        crawler.init(worker)
        mxid = crawler.scan_mxid(choose_one=True)
        crawler.crawler(mxid)


def wait_time(wait_seconds, dst_time):
    dst_time = datetime.datetime.strptime(dst_time, '%Y-%m-%d %H:%M:%S')
    dst_time -= datetime.timedelta(seconds=wait_seconds)
    pid_print(f"Wait until {dst_time}...")
    diff = 0
    while True:
        for i in range(50):
            now_time = datetime.datetime.now()
            diff = dst_time - now_time
            if diff.days < 0: return
            time.sleep(0.1)
        pid_print(f"{diff} remaining")


def scan_site_info(workers):
    worker = workers[0]
    sites = worker.query_all_site_info()
    print(f"Scanning sites, count = {len(sites)}")
    sites_dic = {}
    i = 0
    for sid, name in sites:
        i += 1
        notice, vaccines = worker.query_site_info(sid)
        sites_dic[sid] = {'name': name, 'notice': notice, 'vaccines': vaccines}
        print(f"{i}: {name} loaded.")
        print(f"{i}: {notice}")
        time.sleep(0.5)
    sites_dic = json.loads(json.dumps(sites_dic, ensure_ascii=False))
    with open("./site_data.json", "r", encoding='UTF-8') as json_file:
        old_sites_dic = json.load(json_file)
    print(cmp_json(old_sites_dic, sites_dic))
    os.system("pause")
    with open("./site_data.json", "w", encoding='UTF-8') as json_file:
        json_file.write(json.dumps(sites_dic, ensure_ascii=False, indent=2))


def cmp_json(src_data, dst_data):
    if type(src_data) != type(dst_data):
        return dst_data
    elif isinstance(dst_data, dict):
        differ_dict = {}
        for key, value in dst_data.items():
            if key in src_data:
                differ = cmp_json(src_data[key], value)
                if differ is not None:
                    differ_dict[key] = differ
            else:
                print(type(key))
                differ_dict[key] = value
        return differ_dict if differ_dict else None
    else:
        if str(src_data) != str(dst_data):
            return dst_data
    return None


def pid_print(val):
    print(f"{os.getpid()}: [{datetime.datetime.now().strftime('%S.%f')}]{val}")


def verify_info(worker):
    #pid_print(worker.session_id)
    #pid_print(worker.user_agent)
    worker.test_self()


def watch_date():
    for i in range(2, 30):
        dates.append((datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%Y-%m-%d"))


def watch_vaccine(worker):
    #while True:
    dates = worker.query_vaccine_info()
        #if len(dates) > 0: return dates
        #pid_print(dates)
        #time.sleep(0.4)


if __name__ == '__main__':
    main()
    input('按任意键退出')