import math
import os
import shutil
import time

import cv2
from mss import mss, tools
from numba import jit

from Common.common import OSTool
from Common.common_function import get_current_dir
from Common.log import log


def capture_screen(file_name):
    dir_path = os.path.dirname(file_name)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with mss() as capture:
        capture.shot(mon=-1, output=file_name)
    return file_name


def capture_screen_by_loc(file_path, loc_dic):
    # loc = {"left": 0, "top": 0, "width": 100, "height": 100}
    with mss() as capture:
        img = capture.grab(monitor=loc_dic)
        tools.to_png(img.rgb, img.size, output=file_path)


def get_position_by_pic(name, offset=(10, 10), **kwargs):
    """
    It's a normal function to get a location
    :param name: picture path+name
    :param offset: diy a point
    :return: tuple,such as (12,12)
    """
    if isinstance(name, str) and os.path.isdir(name):
        pic_list = OSTool.get_folder_items(name, file_only=True)
        assert pic_list, "pic is not exist in {}".format(name)
        pic_path_list = list(map(lambda x: name + "/{}".format(x), pic_list))
        name = pic_path_list
    if isinstance(name, list):
        time.sleep(0.5)
        return get_icon_by_pictures(name, offset, **kwargs)
    else:
        time.sleep(0.5)
        return get_icon_by_pic(name, offset, **kwargs)


def get_icon_by_pictures(name, offset=(10, 10), **kwargs):
    """
    sometimes you have several similar pic,but only
    one picture location will be located
    """
    rate = kwargs.get("rate", 0.9)
    for pic in name:
        demo_pic = kwargs.get("demo_picture")
        if not demo_pic:
            capture_screen('demo.png')
            demo_pic = 'demo.png'
        img_name = cv2.imread(pic)
        t = cv2.matchTemplate(cv2.imread(demo_pic), img_name, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(t)

        if max_val > rate:
            x = max_loc[0]
            y = max_loc[1]
            # os.remove('demo.png')
            return (x + offset[0], y + offset[1]), img_name.shape, max_val
        else:
            path = get_current_dir("Test_Data", "temp_log.txt")
            with open(path, "a+") as f:
                f.write("{} {}\n".format(max_val, pic))
            continue
    return None


def get_icon_by_pic(name, offset=(10, 10), **kwargs):
    """
    find a location in a picture by name
    :param name: path+name
    :param offset: diy a point
    :return: (offset:(x,y),shape:(y,x,3))
    """
    rate = kwargs.get("rate", 0.9)
    demo_pic = kwargs.get("demo_picture")
    if not demo_pic:
        capture_screen('demo.png')
        demo_pic = 'demo.png'
    img_name = cv2.imread(name)
    t = cv2.matchTemplate(cv2.imread(demo_pic), img_name,
                          cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(t)
    if max_val > rate:
        x = max_loc[0]
        y = max_loc[1]
        # os.remove('demo.png')
        return (x + offset[0], y + offset[1]), img_name.shape, max_val
    else:
        path = get_current_dir("Test_Data", "temp_log.txt")
        with open(path, "a+") as f:
            f.write("{} {}\n".format(max_val, name))
        return None


def compare_pic_similarity(img, tmp):
    img_name = cv2.imread(img)
    img_tmp = cv2.imread(tmp)
    t = cv2.matchTemplate(img_name, img_tmp, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(t)
    if max_val > 0.9:
        return max_loc, img_name.shape
    return False


def wait_element(name, cycle=3, offset=(10, 10), **kwargs):
    """
    wait a result by looping
    :param offset:
    :param name: path list or a path which you want to locate a point
    :param cycle: loop number
    :return:
    """
    for i in range(cycle):
        rs = get_position_by_pic(name, offset, **kwargs)
        if not rs:
            time.sleep(1)
            continue
        else:
            return rs
    return


def save_from_data(filename, data):
    dir_path = os.path.dirname(filename)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    cv2.imwrite(filename, data)


def compare_picture_auto_collect(screenshot_file, template_file):
    """
    1.check screenshot_file,
    if not exist ,return

    2.check template_file,
    if folder not exist ,create one
    if file not exit ,use source_file

    :param screenshot_file: Full Path
    :param template_file: Full Path
    :return:
    """
    if not os.path.exists(screenshot_file):
        raise Exception("Can not find screenshot_file:{}".format(screenshot_file))

    if not os.path.exists(template_file):
        log.info("can not find template file:{} ,create a new one".format(template_file))
        dirs = os.path.dirname(template_file)
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        shutil.copyfile(screenshot_file, template_file)
    return compare_picture_list(screenshot_file, template_file)


@jit()
def collect_diff_counts(width, height, source, template):
    # i, j are for width and height
    # source is source image
    # template is template image
    diff_count = 0
    for i in range(width):
        for j in range(height):
            if compare_pixel(source[i][j], template[i][j]) > 25:
                diff_count += 1
                source[i][j] = [0, 0, 255]
                continue
    return diff_count, source


def compare_picture(source_file, dest_file):
    source = cv2.imread(source_file)
    dest = cv2.imread(dest_file)
    w, h = source.shape[0], source.shape[1]

    if source.shape != dest.shape:
        return 0.1, []
    else:
        # if 'linux' in platform.platform().lower():
        #     return 0.99
        # else:
        diff_count, diff_res = collect_diff_counts(w, h, source, dest)
        return 1 - diff_count / (w * h), diff_res


def compare_picture_list(source_file, dest_file):
    source = cv2.imread(source_file)
    dest = cv2.imread(dest_file)
    w, h = source.shape[0], source.shape[1]
    if source.shape != dest.shape:
        rs = 0.1, []
    else:
        diff_count, diff_res = collect_diff_counts(w, h, source, dest)
        rs = 1 - diff_count / (w * h), diff_res
        if rs[0] > 0.99:
            return rs
    # check backup picture
    dest_file = os.path.split(dest_file)
    file_name, extend = dest_file[1].split('.')
    for i in range(5):
        join_name = os.path.join(dest_file[0], '{}_{}.{}'.format(file_name, i, extend))
        source = cv2.imread(source_file)
        dest = cv2.imread(join_name)
        w, h = source.shape[0], source.shape[1]
        if not os.path.exists(join_name):
            continue
        if source.shape != dest.shape:
            continue
        else:
            diff_count, diff_res = collect_diff_counts(w, h, source, dest)
            rs = 1 - diff_count / (w * h), diff_res
            log.info(rs[0])
            if rs[0] > 0.99:
                return rs
    return rs


@jit()
def compare_pixel(rgb1, rgb2):
    r = (rgb1[0] - rgb2[0])
    g = (rgb1[1] - rgb2[1])
    b = (rgb1[2] - rgb2[2])
    return math.sqrt(r * r + g * g + b * b)


def hex2rgb(hexcolor):
    rgb = [(hexcolor >> 16) & 0xff,
           (hexcolor >> 8) & 0xff,
           hexcolor & 0xff
           ]
    return rgb


def rgb2hex(rgbcolor):
    r, g, b = rgbcolor
    return (r << 16) + (g << 8) + b


class ComparePic:

    @staticmethod
    def __ahash(file):
        # 缩放为8*8
        img = cv2.imread(file)
        img = cv2.resize(img, (8, 8), interpolation=cv2.INTER_CUBIC)
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # s为像素和初值为0，hash_str为hash值初值为''
        s = 0
        hash_str = ''
        # 遍历累加求像素和
        for i in range(8):
            for j in range(8):
                s = s + gray[i, j]
                # 求平均灰度
        avg = s / 64
        # 灰度大于平均值为1相反为0生成图片的hash值
        for i in range(8):
            for j in range(8):
                if gray[i, j] > avg:
                    hash_str = hash_str + '1'
                else:
                    hash_str = hash_str + '0'
        return hash_str

    # 差值感知算法
    @staticmethod
    def __dhash(file):
        # 缩放8*8
        img = cv2.imread(file)
        img = cv2.resize(img, (9, 8), interpolation=cv2.INTER_CUBIC)
        # 转换灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hash_str = ''
        # 每行前一个像素大于后一个像素为1，相反为0，生成哈希
        for i in range(8):
            for j in range(8):
                if gray[i, j] > gray[i, j + 1]:
                    hash_str = hash_str + '1'
                else:
                    hash_str = hash_str + '0'
        return hash_str

    # Hash值对比
    @staticmethod
    def __cmp_hash(hash1, hash2):
        n = 0
        # hash长度不同则返回-1代表传参出错
        if len(hash1) != len(hash2):
            return -1
        # 遍历判断
        for i in range(len(hash1)):
            # 不相等则n计数+1，n最终为相似度
            if hash1[i] != hash2[i]:
                n = n + 1
        return 1 - n / 64

    @classmethod
    def compare_picture(cls, file, template_folder, similarity=0.7):
        if not os.path.exists(template_folder):
            return 0
        templates = os.listdir(template_folder)
        for template in templates:
            template_name = get_current_dir(template_folder, template)
            h1 = cls.__ahash(file)
            h2 = cls.__ahash(template_name)
            compare = cls.__cmp_hash(h1, h2)
            if compare > similarity:
                return True
        return False


if __name__ == '__main__':
    print(compare_pixel((37, 177, 76), (30, 171, 80)))
    exit()
    my_screenshot_file = r"Z:\WorkSpace3\wes_automation_script\temp.png"
    my_template_file = r"Z:\WorkSpace3\wes_automation_script\win10_p1.jpg"
    try:
        my_res = compare_picture_auto_collect(my_screenshot_file, my_template_file)
        log.info(my_res)
    except Exception as e:
        log.info(e.args)
