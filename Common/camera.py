# -*- coding: utf-8 -*-
# @time     :   2/25/2021 10:59 AM
# @author   :   balance
# @file     :   camera.py
import datetime
import os
import threading
import time

import cv2
import yaml

from Common.common import get_element
from Common.log import log

"""
宽：3：CAP_PROP_FRAME_WIDTH
高：4：CAP_PROP_FRAME_HEIGHT
FPS:5:CAP_PROP_FPS
亮度：10：cv2.CAP_PROP_BRIGHTNESS：0-255
对比度：11：CAP_PROP_CONTRAST：0-255
饱和度：12：CAP_PROP_SATURATION：0-255
增益：14：CAP_PROP_GAIN：0-255
曝光：15：CAP_PROP_EXPOSURE：-11--2
白平衡：17：CAP_PROP_WHITE_BALANCE_BLUE_U：2000-6500
清晰度：20：CAP_PROP_SHARPNESS：0-255
对焦：28：CAP_PROP_FOCUS：0-250
放大：27：CAP_PROP_ZOOM：100-500
逆光对比：32：CAP_PROP_BACKLIGHT：0开-1关
全景（镜头水平移动）：33：CAP_PROP_PAN：-10-10
倾斜（镜头垂直移动）：34：CAP_PROP_TILT：-10-10
打开设置：37：CAP_PROP_SETTINGS：0不开-1开
自动对焦：39：CAP_PROP_AUTOFOCUS：1开-2关
https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
:return:
"""


def get_current_time():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')


def get_current_time_hour():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H')


class CAMERA:
    """
    used for logic camera operation
    """

    def __init__(self, camera_index=1, capture_flag=False, video_path='./Test_data/camera'):
        self.camera_index = self.get_video_device_list()[-1]
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        print(self.cap)
        self.exit = False
        self.temp_screen = None
        if capture_flag:
            if video_path:
                self.writer = self.init_capture(video_path)
            else:
                self.writer = self.init_capture('../Test_Script')
        else:
            self.writer = None
        self.default = self.load_default()

    def load_default(self):
        """
        camera default data form manual setting
        :return:
        """
        with open("./Test_Data/camera/camera_default.yml", 'r') as f:
            return yaml.safe_load(f)

    def __del__(self):
        """
        release camera
        :return:
        """
        cv2.destroyAllWindows()
        self.cap.release()
        if self.writer:
            self.writer.release()

    def get_property(self, list_p):
        """
        get special property
        :param list_p:
        :return:
        """
        cap_info = {}
        for p in list_p:
            cap_info[p] = self.cap.get(p)
        return cap_info

    def set_property(self, data):
        """
        set special property
        :param data:
        :return:
        """
        for key, value in data.items():
            self.cap.set(key, value)

    def screenshot(self, file):
        ret, frame = self.cap.read()
        log.info(f'[camera][screenshot]ret value:{ret}')
        log.info(f'[camera][screenshot]frame value:{ret}')
        cv2.imwrite(file, frame)

    @staticmethod
    def get_video_device_list():
        """
        get all camera device
        :return:
        """
        index = 0
        arr = []
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                break
            else:
                arr.append(index)
            cap.release()
            index += 1
        return arr

    @staticmethod
    def get_format(path):
        """
        get codec from file name
        :param path:
        :return:
        """
        base = os.path.basename(path)
        file_type = base.split(".")[1]
        format_dict = {
            "mp4": "MJPG",
            "avi": "DIVX",
            "wmv": "WMV2"
        }
        t_format = format_dict.get(file_type.lower())
        if t_format:
            return t_format
        else:
            return "X264"

    def init_capture(self, video_path):
        """
        init video writer
        :param video_path:
        :return:
        """
        save_path = os.path.join(video_path, "{}.avi".format(get_current_time_hour()))
        t_format = self.get_format(save_path)
        fourcc = cv2.VideoWriter_fourcc(*t_format)
        out = cv2.VideoWriter(save_path, fourcc, 1, (1280, 720))
        return out

    def get_img(self):
        """
        Used to get pic form camera
        :return:
        """
        ret = None
        frame = None
        for i in range(10):
            ret, frame = self.cap.read()
        if ret:
            self.temp_screen = frame
            if self.writer:
                self.writer.write(frame)
            return frame
        else:
            raise Exception("Fail to get image")

    def show(self):
        """
        used to show real time camera pic
        :return:
        """
        while (True):
            if self.temp_screen is not None:
                cv2.imshow('frame', self.temp_screen)
                cv2.waitKey(1)
            if cv2.waitKey(1) == ord('q'):
                break
            if self.exit:
                break
            time.sleep(0.2)

    def show_t(self):
        """
        start show thread
        :return:
        """
        t = threading.Thread(target=self.show_test)
        t.start()

    def show_test(self):
        """
        used to debug show
        :return:
        """
        while (True):
            ret, frame = self.cap.read()
            if ret:
                cv2.imshow('frame', frame)
                cv2.waitKey(1)
            else:
                raise Exception("Fail to get image")
            if cv2.waitKey(1) == ord('q'):
                break
            time.sleep(0.2)


def check_video_exist(check_cycle: int = 30, wait_time: int = 1):
    for i in range(check_cycle):
        frame_window = get_element('FRAM_WINDOW')
        if frame_window.Exists():
            log.info('[check_video_exist] open frame windows successful')
            return True
        else:
            time.sleep(wait_time)
            continue
    log.error('[check_video_exist] found fram windows time out')
    return False
