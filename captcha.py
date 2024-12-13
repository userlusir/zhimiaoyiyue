import json
import math
import os
import random

import cv2
import numpy as np
import customex

src_images = []
src_kp_des = []

slider_image = None


def init(folder_path):
    global src_images, src_kp_des, slider_image
    files = os.listdir(folder_path)
    src_images = [cv2.imread(os.path.join(folder_path, file), cv2.IMREAD_UNCHANGED) for file in files if file != "slider.png"]
    #for image in src_images:
    #    cv2.imshow("666", image)
    #    cv2.waitKey(0)
    src_kp_des = [sift_kp(image) for image in src_images]
    slider_image = cv2.imread(os.path.join(folder_path, "slider.png"), cv2.IMREAD_UNCHANGED)
    slider_image = cv2.cvtColor(slider_image, cv2.COLOR_BGR2GRAY)


def solve(resp, debug_mode=0):
    if len(src_kp_des) == 0 or slider_image is None:
        raise Exception("haven't inited")
    import base64
    image = base64.b64decode(resp["dragon"])
    image = np.frombuffer(image, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)
    try:
        if "tiger" in resp and resp["tiger"] is not None and len(resp["tiger"]) > 0:
            return find_notch(image, debug_mode)
        else:
            return find_degree(image, debug_mode)
    except (cv2.error, customex.MatchNotFoundError) as ex:
        from datetime import datetime
        cv2.imwrite(f"./notfound/{int(datetime.now().timestamp() * 1000)}.png", image)
        if isinstance(ex, cv2.error):
            ex = customex.MatchNotFoundError(f"cv2.error:{ex}")
        raise ex


def find_notch(bg_img, debug_mode=0):
    bg_img = bg_img[:, :, :3]

    bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
    _, bg_gray = cv2.threshold(bg_gray, 254, 255, cv2.THRESH_BINARY)
    res = cv2.matchTemplate(bg_gray, slider_image, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if debug_mode > 0:
        print(max_val, max_loc)
        rows, cols = slider_image.shape
        x, y = max_loc
        bg_img[y:cols+y, x:rows+x, 0] = slider_image
        bg_img[y:cols+y, x:rows+x, 1] = slider_image
        bg_img[y:cols+y, x:rows+x, 2] = slider_image
        cv2.imshow("666", bg_img)
        cv2.waitKey(0)

    if max_val is not None:
        return max_loc[0]
    raise customex.MatchNotFoundError("Cannot match notch")


def find_degree(dst_img, debug_mode=0):
    dst = sift_kp(dst_img)
    goods = [sift_match(src, dst) for src in src_kp_des]
    index, good = max(enumerate(goods), key=lambda elem: len(elem[1]))
    try:
        if len(good) > 4:
            return sift_degree(src_images[index], dst_img, src_kp_des[index], dst, good, debug_mode)
    except (cv2.error, np.linalg.LinAlgError) as ex:
        raise customex.MatchNotFoundError(str(ex))
    raise customex.MatchNotFoundError("cannot match any image")


def sift_degree(img1, img2, kp_des1, kp_des2, good, debug_mode=0):
    kp1, _ = kp_des1
    kp2, _ = kp_des2
    ptsA = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    ptsB = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    ransacReprojThreshold = 4
    H, _ = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransacReprojThreshold)
    H = np.linalg.inv(H)  # 求逆矩阵

    enum_points = [(135, 0, 0), (45, 200, 0), (315, 200, 200), (225, 0, 200)]
    center = calc_match_point(H, (100, 100))
    result = []
    for point in enum_points:
        result.append(calc_degree(point[0], center, calc_match_point(H, point[1:])))
    result = np.array(result)

    if debug_mode > 0:
        print(np.var(result))
        if debug_mode == 1:
            img3 = cv2.warpPerspective(img2, H, (img1.shape[1], img1.shape[0]), flags=cv2.INTER_LINEAR)
            img4 = cv2.addWeighted(img1, 0.5, img3, 0.5, 0)
            cv2.imshow("captcaha", img4)
        if debug_mode == 2:
            img3 = rotate_image(img2, np.mean(result))
            img4 = cv2.hconcat([img2, img3])
            cv2.putText(img4, str(np.mean(result)), (350, 10), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255), 1)
            cv2.imshow("captcaha", img4)
        if debug_mode == 3:
            img_bg = np.empty((max(img1.shape[0], img2.shape[0]), img1.shape[1] + img2.shape[1], 3), dtype=np.uint8)
            img_bg[0:img1.shape[0], 0:img1.shape[1]] = img1[:, :, :3]
            img_bg[0:img2.shape[0], img1.shape[1]:img1.shape[1]+img2.shape[1]] = img2[:, :, :3]
            img_match = cv2.drawMatches(img1, kp1, img2, kp2, good, None, flags=0)
            img_out = cv2.addWeighted(img_bg, 0.5, img_match, 0.5, 0)
            cv2.imshow("captcaha", img_out)
        if np.var(result) > 500:
            raise customex.MatchNotFoundError
        else:
            cv2.waitKey(1)
    return np.mean(result)


def sift_kp(image):
    # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # sift = cv2.xfeatures2d_SIFT.create()
    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(image, None)
    # kp_image = cv2.drawKeypoints(gray_image, kp, None)
    return kp, des


def sift_match(kp_des1, kp_des2):
    kp1, des1 = kp_des1
    kp2, des2 = kp_des2
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m, n in matches:
        if m.distance < 0.4 * n.distance:
            good.append(m)
    return good


def calc_match_point(H, location):
    a = list(location)
    a.append(1)
    a = np.array(a).reshape(3, 1)
    b = tuple(np.matmul(H, a)[:, 0][:2])
    return b


def calc_degree(base_degree, loc1, loc2):
    k = -(loc1[1] - loc2[1]) / (loc1[0] - loc2[0])  # 坐标系转换 加负号
    degree = math.atan(k) / math.pi * 180.0
    if loc1[0] > loc2[0]:
        degree = 180.0 + degree
    degree = base_degree - degree
    if degree < 0.0: degree += 360
    if degree > 360.0: degree -= 360
    return 360 - degree


def rotate_image(image, degree):
    h, w = image.shape[:2]  # 10
    center = (w // 2, h // 2)  # 11
    M = cv2.getRotationMatrix2D(center, degree, 1.0)
    return cv2.warpAffine(image, M, (w, h))


def test_images():
    init("./match")
    print("Input source dir:")
    folder_path = "E:/Users/yanzheng/new/1/all" #input()
    print("Input target dir:")
    target_path = "E:/Users/yanzheng/new/1/out" #input()
    files = os.listdir(folder_path)
    import time
    print(f"Image count: {len(files)}")
    t_start = time.perf_counter()
    for file in files:
        image = cv2.imread(os.path.join(folder_path, file), cv2.IMREAD_UNCHANGED)
        file = file.replace("jpg", "png")
        try:
            result = find_degree(image, debug_mode=2)
            if len(target_path) > 1:
                rotated = rotate_image(image, result)
                cv2.imwrite(os.path.join(target_path, file), rotated, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
        except (cv2.error, customex.MatchNotFoundError) as ex:
            print(file)
            cv2.imwrite(os.path.join("./notfound", file), image)
    print(f"Time used: {time.perf_counter() - t_start:05.2f}")


if __name__ == '__main__':
    init("./match")
    #with open("test.txt") as file:
    #    print(solve(json.load(file), debug_mode=1))
    test_images()






















