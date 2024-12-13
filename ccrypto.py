from datetime import datetime, timedelta
from hashlib import md5
import json

from main import pid_print
import customex

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
import time
import subprocess
import logging
from datetime import datetime
import http.client

GMT_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
delta = 0
changed = False

def zftsl_update(time):
    global delta
    post_time = (datetime.strptime(time, GMT_FORMAT) + timedelta(hours=8)).timestamp()
    now_time = datetime.now().timestamp()
    delta = post_time - now_time


def zftsl_generate():
    now_time = str(int(datetime.now().timestamp() + delta))
    return md5(("zfsw_" + now_time[:-1]).encode("utf8")).hexdigest()


def pkcs7_unpadding(padded_data):
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data)
    try:
        uppadded_data = data + unpadder.finalize()
    except ValueError:
        raise Exception('无效的加密信息!')
    else:
        return uppadded_data

class System_Time:

    def __init__(self):
        self.__newtime = None

    @property
    def newtime(self):
        return self.__newtime

    @newtime.setter
    def newtime(self, value):
        self.__newtime = value

    def get_sys_now_time(self):
        return datetime.strftime(datetime.now(),"%H:%M:%S")

    def get_webservertime(self, host='183.230.139.228'):
        conn = http.client.HTTPConnection(host)
        conn.request("GET", "/")
        r = conn.getresponse()
        # r.getheaders() #获取所有的http头
        ts = r.getheader('date')  # 获取http头date部分
        # 将GMT时间转换成北京时间
        ltime = time.strptime(ts[5:25], "%d %b %Y %H:%M:%S")
        # print(ltime)
        ttime = time.localtime(time.mktime(ltime) + 8 * 60 * 60)
        # print(ttime)
        dat = "%u-%02u-%02u" % (ttime.tm_year, ttime.tm_mon, ttime.tm_mday)
        tm = "%02u:%02u:%02u" % (ttime.tm_hour, ttime.tm_min, ttime.tm_sec)
        # print("dat:{}".format(dat))
        #pid_print("tm:{}".format(tm))
        return tm

    @classmethod
    def alter(cls):
        obj = cls()
        webtm = obj.get_webservertime()
        obj.newtime = webtm
        # print(obj.newtime)
        try:
            ps = subprocess.Popen(
                'time',
                universal_newlines=True,
                shell=True,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

            ps.communicate(obj.newtime, 15)
            logging.basicConfig(level=logging.NOTSET)
            if ps.poll() is not None:
                logging.info("进程成功终止")
            else:
                logging.warning("进程未终止")

            if ps.returncode == 0:
                logging.info("系统时间修改成功")
            elif ps.returncode > 0:
                logging.warning("进程异常:{}".format(ps.returncode))
            elif ps.returncode < 0 or ps.returncode > 10000:
                logging.error("进程错误")
        except Exception as error:
            pid_print(error.__str__())


if __name__ == '__main__':
    System_Time.alter()