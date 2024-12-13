import base64
import json
import random
import re
import time
import sys
from datetime import datetime

import cv2
import numpy as np
import requests

import captcha
import customex
import ccrypto
from main import pid_print

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

requests.packages.urllib3.disable_warnings()

last_info = None

def get_info():
    global last_info
    changed = False
    try:
        with open("./data.json", "r", encoding="UTF-8") as data_file:
            infos = json.load(data_file)
            if last_info is not None and len(infos) > 0 and last_info == infos[0]:
                changed = True
                last_info = None
                infos.pop()
            if len(infos) > 0:
                last_info = infos[0]
            else:
                raise customex.AccountDataEmptyError("没有用户信息")
    finally:
        if changed:
            with open("./data.json", "w", encoding="UTF-8") as data_file:
                json.dump(infos, data_file)
    return last_info


def try_get_info(interval=3.0):
    while True:
        try:
            return get_info()
        except customex.AccountDataEmptyError:
            print("Account data is empty.")
            time.sleep(interval)


def get_ua():
    ua_list = [
        "Mozilla/5.0 (Linux; Android 7.1.1; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 7.1.1; OD103 Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 6.0.1; SM919 Build/MXB48T; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 5.1; HUAWEI TAG-AL00 Build/HUAWEITAG-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043622 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 7.1.1; OD103 Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 6.0.1; SM919 Build/MXB48T; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043632 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 5.1; HUAWEI TAG-AL00 Build/HUAWEITAG-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.49 Mobile MQQBrowser/6.2 TBS/043622 Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001126) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 10; CDY-AN90 Build/HUAWEICDY-AN90; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200801 Mobile Safari/537.36 MMWEBID/4006 MicroMessenger/7.0.18.1740(0x2700123B) Process/toolsmp WeChat/arm64 NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 10; JEF-AN00 Build/HUAWEIJEF-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/8362 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001126) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 9; PBEM00 Build/PKQ1.190519.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/4773 MicroMessenger/7.0.19.1760(0x27001335) Process/toolsmp WeChat/arm64 NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 8.0.0; BLA-AL00 Build/HUAWEIBLA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2690 MMWEBSDK/200401 Mobile Safari/537.36 MMWEBID/3762 MicroMessenger/7.0.14.1660(0x27000EC6) Process/toolsmp NetType/WIFI Language/zh_CN ABI/arm64 WeChat/arm32",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001124) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 10; ELE-AL00 Build/HUAWEIELE-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/215 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/4902 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 9; vivo X21A Build/PKQ1.180819.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/6397 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 9; PAR-AL00 Build/HUAWEIPAR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/6007 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 10; VOG-AL00 Build/HUAWEIVOG-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/8872 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 9; DUK-AL20 Build/HUAWEIDUK-AL20; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200901 Mobile Safari/537.36 MMWEBID/2591 MicroMessenger/7.0.19.1760(0x2700133F) Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 8.1.0; DUA-TL00 Build/HONORDUA-TL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2690 MMWEBSDK/200502 Mobile Safari/537.36 MMWEBID/2494 MicroMessenger/7.0.15.1680(0x27000F50) Process/toolsmp WeChat/arm32 NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.14(0x17000e2e) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 8.1.0; MI 5X Build/OPM1.171019.019; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2691 MMWEBSDK/200801 Mobile Safari/537.36 MMWEBID/9633 MicroMessenger/7.0.18.1740(0x2700123B) Process/toolsmp WeChat/arm64 NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 12_4_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001124) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.15(0x17000f31) NetType/4G Language/zh_TW",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001124) NetType/WIFI Language/zh_CN",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.17(0x17001124) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 10; MI 8 SE Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045512 Mobile Safari/537.36 MMWEBID/1299 MicroMessenger/8.0.1840(0x28000039) Process/tools WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 10; PBCM10 Build/QKQ1.191224.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045513 Mobile Safari/537.36 MMWEBID/1571 MicroMessenger/8.0.1.1841(0x2800013A) Process/tools WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.1(0x1800012a) NetType/4G Language/zh_CN",
        "Mozilla/5.0 (Linux; Android 10; V1923A Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045514 Mobile Safari/537.36 MMWEBID/979 MicroMessenger/8.0.1.1841(0x2800015A) Process/tools WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 9; 16s Pro Build/PKQ1.190616.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2757 MMWEBSDK/201201 Mobile Safari/537.36 MMWEBID/8031 MicroMessenger/7.0.22.1820(0x27001639) Process/appbrand0 WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64",
        "Mozilla/5.0 (Linux; Android 10; ELS-NX9 Build/HUAWEIELS-N29; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2759 MMWEBSDK/201201 Mobile Safari/537.36 MMWEBID/1583 MicroMessenger/8.0.1.1840(0x2800013B) Process/tools WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64"
    ]

    ualist = ['Mozilla/5.0 (Linux; Android 11.5.6; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.3.5285.724 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.10.4; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.3.9538.391 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.4.0; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.6.7498.463 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.3.2; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/19.7.8987.289 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.10.6; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/94.2.9589.832 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.8.5; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.5.9987.428 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.9.0; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/21.3.5923.787 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.3; MI 4 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/69.0.7476.318 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.8.7; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/45.3.8314.188 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.6.2; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/43.7.6255.131 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.1.7; MI 4 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.7.9749.227 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.1.0; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.1.4424.652 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.3.8; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.1.5143.822 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.4.8; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/65.8.4916.254 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.3.2; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/42.3.2989.345 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.10.1; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/47.1.4619.936 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.8; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.7712.691 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.7.8; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/36.4.1648.735 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.1.4; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.8.8428.872 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.1.3; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/16.7.7764.455 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.6.5; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/99.5.5679.272 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.3.6; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.2.2196.747 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.10.6; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.0.8241.831 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.10.10; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.8.9992.554 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.9.0; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.4.8789.679 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.4.2; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/37.8.6734.312 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.2.7; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.3.9471.535 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.7.9; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.7.3471.896 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.3.0; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.8.8853.456 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.9.5; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/22.2.8576.987 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.8.7; MI 4 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/81.8.9598.944 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.1.1; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.6.7627.891 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.3.7; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.6.2497.113 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.9.0; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/48.3.5633.437 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.3.6; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.1.1632.738 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.7.9; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/27.0.7467.674 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.1.7; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/13.8.6458.327 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.6.1; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/88.3.1234.435 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.1.2; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.5.7988.753 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.2.1; MI 4 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.9.9298.926 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.8.2; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/11.3.7753.416 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.6.1; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.2.9579.341 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.8.8; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.4.2955.431 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.3.9; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.6.2132.245 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.10.7; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.6.7817.111 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.7.3; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.8.6931.331 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.2.4; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.6.3136.892 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.10.7; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/26.0.5442.574 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.8.0; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.2.2495.191 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.4.1; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/37.1.8331.185 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.3.1; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.2.7754.166 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.3.9; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/56.9.5285.728 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.7.10; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.4.1436.827 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.6.8; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/18.5.9839.597 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.4.5; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/21.6.2988.372 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.0.5; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/29.7.1898.675 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.7.7; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/13.6.1154.165 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.4.5; MI 4 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.4.6533.951 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.2.1; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/34.1.9929.638 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.8.2; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.1.3253.579 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.10; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/48.3.5731.226 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.5.5; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/99.0.8698.543 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.6.1; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.4.3128.175 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.2.7; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/71.2.1414.925 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.4.0; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.2.5351.745 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.4.3; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/11.0.1532.378 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.5.4; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/73.6.3556.616 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.0.9; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/73.6.4219.849 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.1.4; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/45.3.2876.928 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.2.4; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/26.9.6426.241 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.0.9; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/34.0.6277.217 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.3.2; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/38.0.8125.279 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.4.2; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/47.4.8559.318 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.8; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.5.6358.252 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.4.2; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/11.6.5748.118 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.6.1; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/25.0.6191.683 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.4.0; MI 8 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.8.8524.758 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.2.3; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.4.6969.489 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.5; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.5722.643 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.2.8; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/34.2.3718.372 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.0.4; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/13.6.9693.917 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.8.10; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.6.7395.983 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.2.7; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/37.8.3534.265 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.6.5; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/21.9.5398.433 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.3.8; MI 5 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/71.7.4127.621 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 10.2.6; MI 7 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/95.2.5338.471 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.9.10; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/82.0.2785.524 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.10.2; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/64.5.3677.247 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.10.10; MI 3 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/29.8.2223.719 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.9.4; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.9.3816.589 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.3.0; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4388.761 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.4.7; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/93.6.3558.759 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.0.4; MI 2 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/12.6.8577.148 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 9.2.10; MI 0 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.4.5886.195 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 8.3.4; MI 11 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/94.6.5944.513 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.0.2; MI 6 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/88.4.9524.615 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.10.6; MI 10 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/46.7.6263.463 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.2.7; MI 9 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.1.2123.116 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 11.2.4; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/64.0.3434.569 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN', 'Mozilla/5.0 (Linux; Android 7.4.2; MI 1 Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.8.8199.253 MQQBrowser/6.2 TBS/043807 Mobile Safari/537.36 MicroMessenger/6.6.1.1220(0x26060135) NetType/WIFI Language/zh_CN']
    ua = random.choice(ualist)
    return ua


def get_worker(code_list=None, AES_key=None, site_id=0, vaccine_text=None):
    return NetWorker(code_list, AES_key, site_id, vaccine_text)


def try_get_worker(code_list=None, AES_key=None, site_id=0, vaccine_text=None, interval=3.0):
    return NetWorker(code_list, AES_key, site_id, vaccine_text)


class NetWorker:

    def __init__(self, code_list, AES_key, site_id, vaccine_text):
        self.code_list = code_list
        self.AES_key = AES_key
        self.site_id = site_id
        self.vaccine_text = vaccine_text
        self.ftime = 1
        self.public_url = "https://183.230.139.228:443//sc/wx/HandlerSubscribe.ashx?"
        self.post_url = "https://183.230.139.228:443//sc/api/"
        self.public_headers = {
            "Host": "api.cn2030.com",
            "Connection": "keep-alive",
            "content-type": "application/json",
            "charset": "utf-8",
            "Accept-Encoding": "gzip, compress, br, deflate",
            "User-Agent": get_ua(),
            "Referer": "https://servicewechat.com/wx2c7f0f3c30d99445/97/page-frame.html"
        }
        self.vaccine_id = None
        self.mxid = None
        self.dates = None
        self.person_info = None
        self.session = requests.Session()
        self.public_headers['Accept'] = None

    def AES_encrypt(self, text):
        length = 16
        AES_key = self.AES_key
        AES_iv = "1234567890000000".encode('utf-8')  # 偏移量
        AES_mode = AES.MODE_CBC
        pad = lambda s: s + (length - len(s.encode('utf-8')) % length) * chr(length - len(s.encode('utf-8')) % length)
        cryptor = AES.new(AES_key, AES_mode, AES_iv)
        plain_text = cryptor.encrypt(pad(text).encode('utf-8'))
        return plain_text.hex()


    def AES_decrypt(self, text):
        AES_key = self.AES_key
        AES_iv = "1234567890000000".encode('utf-8')  # 偏移量
        AES_mode = AES.MODE_CBC
        cryptor = AES.new(AES_key, AES_mode, AES_iv)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return bytes.decode(plain_text).rstrip("\x01").\
            rstrip("\x02").rstrip("\x03").rstrip("\x04").rstrip("\x05").\
            rstrip("\x06").rstrip("\x07").rstrip("\x08").rstrip("\x09").\
            rstrip("\x0a").rstrip("\x0b").rstrip("\x0c").rstrip("\x0d").\
            rstrip("\x0e").rstrip("\x0f").rstrip("\x10")


    def try_get(self, url, handle_status=None, decrypt=False):
        while True:
            try:
                target_url = self.public_url + url
                self.public_headers['zftsl'] = ccrypto.zftsl_generate()
                resp = self.session.get(url=target_url, headers=self.public_headers, verify=False, timeout=1)
                ccrypto.zftsl_update(resp.headers['Date'])
                resp.raise_for_status()
                if decrypt:
                    r_json = json.loads(self.AES_decrypt(resp.text))
                    #pid_print(r_json)
                else:
                    r_json = resp.json()
                if r_json['status'] != 200 and r_json['status'] != 0:
                    raise customex.StatusError(r_json)#(resp.text)
                if url == "act=GetOrderStatus" and r_json['status'] != 200:
                    #time.sleep(1)
                    raise customex.StatusError(r_json)
                if 'Set-Cookie' in resp.headers:
                    self.public_headers['Cookie'] = resp.headers['Set-Cookie']
                if 'user' in r_json:
                    user = r_json["user"]
                    self.person_info = "birthday=" + user["birthday"] + "&tel=" + user["tel"] + "&sex=2&cname=" + user["cname"] + "&doctype=1&idcard=" + user["idcard"]
                #if f"act=GetCustSubscribeDateAll&pid={self.vaccine_id}&id={self.site_id}&month=" in url and 'list' not in r_json:
                    #raise KeyError
                if resp.status_code == 302:
                    self.true_url = resp.headers['Location'][29:]
                #pid_print(r_json)
                return r_json
            except customex.StatusError as ex:
                pid_print(ex)
                if handle_status is not None and r_json['status'] == handle_status:
                    time.sleep(1)
                    raise ex
                if r_json['status'] == 408:
                    self.public_headers['Cookie'] = f"ASP.NET_SessionId={self.get_session_id()}"
                if r_json['status'] == 503:
                    time.sleep(1)
                    pass
                else:
                    pass#time.sleep(0.2)
            except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as ex:
                pid_print(ex)
                #time.sleep(0.2)
                pass
            except json.decoder.JSONDecodeError as ex:
                #pid_print(r_json)#resp.text)
                pid_print(ex)
                time.sleep(0.1)
                pass
            except requests.exceptions.ProxyError:pass
            except KeyError:
                time.sleep(1)
                pass
            except:pass


    def try_post(self, url, data, handle_status=None):
        while True:
            try:
                target_url = self.post_url + url
                self.public_headers['zftsl'] = ccrypto.zftsl_generate()
                resp = self.session.post(url=target_url, data=data, headers=self.public_headers, verify=False, timeout=1)
                ccrypto.zftsl_update(resp.headers['Date'])
                resp.raise_for_status()
                r_json = resp.json()
                if r_json['status'] != 200 and r_json['status'] != 0:
                    raise customex.StatusError(r_json)#(resp.text)
                if 'Set-Cookie' in resp.headers:
                    self.public_headers['Cookie'] = resp.headers['Set-Cookie']
                #pid_print(r_json)
                return r_json
            except customex.StatusError as ex:
                pid_print(ex)
                if handle_status is not None and r_json['status'] == handle_status:
                    raise ex
                elif r_json['status'] == 408:
                    time.sleep(1)
                    self.public_headers['Cookie'] = f"ASP.NET_SessionId={self.get_session_id()}"
                elif r_json['status'] == 503:
                    time.sleep(0.6)
                    pass
                else:
                    pass#time.sleep(0.2)
            except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as ex:
                pid_print(ex)
                #time.sleep(0.2)
                pass
            except json.decoder.JSONDecodeError as ex:
                #pid_print(r_json)#resp.text)
                pid_print(ex)
                time.sleep(0.1)
                pass
            except requests.exceptions.ProxyError:pass
            except:pass


    def test_self(self):
        #resp = self.try_get(f"act=CustomerProduct&id={self.site_id}")
        #vaccines = [(elem['text'], elem['date'], elem['enable']) for elem in resp['list'] if elem['id'] == self.vaccine_id]
        #pid_print(resp['cname'])
        #pid_print(vaccines)
        from re import search
        name = search(r"cname=(.*?)&", self.person_info).group(1)
        sex = search(r"sex=(.*?)&", self.person_info).group(1).replace("2", "女")
        birthday = search(r"birthday=(.*?)&", self.person_info).group(1)
        tel = search(r"tel=([0-9]*?)&", self.person_info).group(1)
        id_card = search(r"idcard=([0-9Xx]*)", self.person_info).group(1)
        if search(r"doctype=([0-9]*)", self.person_info).group(1) != "1": raise Exception("doctype wrong.")
        pid_print(f"{name} ({sex}, {birthday}, {tel}, {id_card}): test passed.")
        self.data = {"birthday":f"{birthday}","tel":f"{tel}","sex":f"{sex}","cname":f"{name}","doctype":1,"idcard":f"{id_card}","mxid":"","date":"","pid":f"{self.vaccine_id}","Ftime":self.ftime,"guid":""}


    def auto_reserve(self, dates=None):
        while True:
            try:
                if dates is not None:
                    random.shuffle(dates)
                    for date in dates:
                        #time.sleep(0.5)
                        mxids = self.query_date_info(date)
                        for mxid in mxids:
                            #time.sleep(0.5)
                            if self.submit_appointment(date, mxid):
                                raise customex.Success()
                        pid_print("No vaccine available.")
                #else:
                    #self.submit_appointment("2021-12-20", self.mxid)
                    #raise customex.Success()
            except customex.Success:
                name = re.search(r"&cname=(.*?)&", self.person_info).group(1)
                pid_print(f"{name} 预约成功!")
                break

    def choice_code(self):
        code = random.choice(self.code_list)
        self.code_list.remove(code)
        return code

    def get_session_id(self):
        try:
            code = self.choice_code()
            url = f"{self.public_url}act=auth&code={code}"
            self.public_headers["zftsl"] = ccrypto.zftsl_generate()
            data = {'rawdata': '{"nickName":"微信用户","gender":0,"language":"","city":"","province":"","country":"","avatarUrl":"https://thirdwx.qlogo.cn/mmopen/vi_32/POgEwh4mIHO4nibH0KlMECNjjGxQUq24ZEaGT4poC6icRiccVGKSyXwibcPq4BWmiaIGuG1icwxaQX6grC9VemZoJ8rg/132"}'}
            resp = self.session.post(url=url, json=data, headers=self.public_headers, verify=False)
            resp = resp.json()
            return resp['sessionId']
        except:pass

    def get_persson_info(self, sessionid=None):
        while sessionid is None:
            sessionid = self.get_session_id()
            if sessionid is None: time.sleep(1)
        try:
            self.try_get(f"act=User")
        except:pass

    def query_all_site_info(self):
        resp = self.try_get("act=CustomerList&city=%5B%22%22%2C%22%22%2C%22%22%5D&lat=22.78658&lng=108.49693&id=0&cityCode=0&product=0")
        sites = [(elem['id'], elem['cname']) for elem in resp['list']]
        return sites

    def query_site_info(self):
        resp = self.try_get(f"act=CustomerProduct&id={self.site_id}")
        vaccines = [(elem['text'], elem['date'], elem['enable']) for elem in resp['list']
                    if elem['text'].startswith("九价") or elem['text'].startswith("四价") or elem['text'].startswith("二价")]
        return resp, vaccines

    def submit_month(self):
        while self.vaccine_id is None:
            self.get_vaccine_id()
            if self.vaccine_id is None: time.sleep(1)
        #self.query_vaccine_info()
        dates = self.get_dates()
        return dates

    def line(self):
        self.try_get(f"act=CustomerProduct&id={self.site_id}")
        self.query_vaccine_info()

    def lines(self):
        self.try_get(f"act=CustomerProduct&id={self.site_id}")
        month = time.strftime("%Y%m", time.localtime())
        self.try_get(f"act=GetCustSubscribeDateAll&pid={self.vaccine_id}&id={self.site_id}&month={month}")

    def get_dates(self):
        while self.dates is None:
            self.query_vaccine_info()
            if self.dates is None: time.sleep(0.7)
        return self.dates

    def get_vaccine_id(self):
        resp = self.try_get(f"act=CustomerProduct&id={self.site_id}", handle_status=503)
        try:
            for elem in resp['list']:
                if self.vaccine_text == elem['text']:
                    self.vaccine_id = elem['id']
                    self.data['pid'] = self.vaccine_id
        except KeyError:pass

    def query_vaccine_info(self):
        month = time.strftime("%Y%m", time.localtime())
        try:
            resp = self.try_get(f"act=GetCustSubscribeDateAll&pid={self.vaccine_id}&id={self.site_id}&month={month}", handle_status=503)
            dates = [elem['date'] for elem in resp['list'] if elem['enable']]
            self.dates = dates
        except KeyError:pass

    def query_date_info(self, date):
        self.true_url = f"act=GetCustSubscribeDateDetail&pid={self.vaccine_id}&id={self.site_id}&scdate={date}"
        resp = self.try_get(self.true_url, handle_status=503, decrypt=True)
        infos = resp['list']
        infos.sort(key=lambda elem: elem['qty'])
        infos = [elem['mxid'] for elem in infos if elem['qty'] > 0]
        infos.reverse()
        return infos

    def submit_appointment(self, date, mxid):
        resp = self.try_get(f"act=GetCaptcha&mxid={mxid}", handle_status=503)
        self.data['mxid'] = f"{mxid}"
        self.data['date'] = f"{date}"
        if resp['status'] == 200:
            try:
                resp = self.try_post(f"User/OrderPost", data=self.AES_encrypt(json.dumps(self.data, ensure_ascii=False).replace(' ','')), handle_status=201)
                if resp['status'] == 200:
                    time.sleep(1)
                    self.try_get("act=GetOrderStatus")
                    return True
            except customex.StatusError:
                pass
        else:
            try:
            # 验证码可旋转0-415度，degree最大为360度，无需转换
                degree = int(captcha.solve(resp))
                #time.sleep(0.6)
                resp_guid = self.try_get(f"act=CaptchaVerify&token=&x={degree}&y=5&mxid={mxid}", handle_status=204, decrypt=True)
                self.data['guid'] = resp_guid['guid']
                #time.sleep(1)
                resp = self.try_post(f"User/OrderPost", data=self.AES_encrypt(json.dumps(self.data, ensure_ascii=False).replace(' ', '')), handle_status=201)
                if resp['status'] == 200:
                    #time.sleep(1)
                    self.try_get("act=GetOrderStatus")
                    return True
            except (customex.MatchNotFoundError, customex.StatusError) as ex:
                pid_print(ex)

    def solve_captcha(self, mxid, data):
        try:
            # 验证码可旋转0-415度，degree最大为360度，无需转换
            degree = int(captcha.solve(data))
            time.sleep(0.6)
            resp = self.try_get(f"act=CaptchaVerify&token=&x={degree}&y=5&mxid={mxid}", handle_status=204, decrypt=True)
            return resp['guid']
        except (customex.MatchNotFoundError, customex.StatusError) as ex:
            pid_print(ex)

