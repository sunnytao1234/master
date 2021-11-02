# todo:develop and debug
import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
import typing
from abc import ABCMeta, abstractmethod
from collections import namedtuple

import PIL.Image
import cv2
import numpy
import wakeonlan
from PIL import Image

from Common.common import is_admin, switch_to_new_user
from Common.common_function import get_current_dir, AddStartup
from Common.log import log
from Common.man import Man
from Test_Script.base import socket_action

BootResult = namedtuple('BootResult',
                        ('startup_time', 'hp_logo_time', 'desktop_time'))
ReBootResult = namedtuple('ReBootResult',
                          ('desktop_time', 'shutdown_time',
                           'hp_logo_time', 'next_desktop_time'))


class DHash:
    @staticmethod
    def calculate_hash(image):
        difference = DHash.__difference(image)

        decimal_value = 0
        hash_string = ""

        for index, value in enumerate(difference):
            if value:
                decimal_value += value * (2 ** (index % 8))

            if index % 8 == 7:
                hash_string += str(hex(decimal_value)[2:].rjust(2, "0"))
                decimal_value = 0

        return hash_string

    @staticmethod
    def hamming_distance(first, second):
        if isinstance(first, str):
            return DHash.__hamming_distance_with_hash(first, second)

        image1_difference = DHash.__difference(first)
        image2_difference = DHash.__difference(second)

        hamming_distance = 0
        for index, img1_pix in enumerate(image1_difference):
            img2_pix = image2_difference[index]

            if img1_pix != img2_pix:
                hamming_distance += 1

        return hamming_distance

    @staticmethod
    def __difference(image):
        resize_width = 9
        resize_height = 8

        smaller_image = image.resize((resize_width, resize_height))
        grayscale_image = smaller_image.convert("L")
        pixels = list(grayscale_image.getdata())

        difference = []
        for row in range(resize_height):
            row_start_index = row * resize_width
            for col in range(resize_width - 1):
                left_pixel_index = row_start_index + col
                difference.append(pixels[left_pixel_index] > pixels[left_pixel_index + 1])

        return difference

    @staticmethod
    def __hamming_distance_with_hash(dhash1, dhash2):
        difference = (int(dhash1, 16)) ^ (int(dhash2, 16))

        return bin(difference).count("1")


class Camera:
    def __init__(self, device_index: int = 1, width: int = 960, height: int = 540):
        self.__width = width
        self.__height = height

        self.__device_index = device_index

        self.__cap = cv2.VideoCapture(self.__device_index, cv2.CAP_DSHOW)
        # self.__cap.set(3, self.__width)  # width
        # self.__cap.set(4, self.__height)  # height

    @classmethod
    def get_device_dict(cls) -> dict:
        device_dict = {
            'device_count': 0,
            'device_list': None
        }
        results = subprocess.run("powershell Get-PnpDevice -Class Camera | ConvertTo-Json".split(), capture_output=True)
        results = json.loads(results.stdout)
        results = [result for result in results if result['Status'] == 'OK']

        device_dict['device_count'] = len(results)
        device_dict['device_list'] = results

        return device_dict

    @staticmethod
    def get_device_list() -> list:
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

    def get_frame(self):
        ret, frame = self.__cap.read()
        if ret:
            frame = cv2.resize(frame, (self.__width, self.__height))
            return frame
        else:
            log.error(f"[Camera][get_frame]cannot get frame from camera device:{self.__device_index}")
            return None

    def show_frame(self, frame_rate: int = 20):
        while True:
            if cv2.waitKey(1) == ord('q'):
                break

            ret, frame = self.__cap.read()
            if ret:
                cv2.imshow('frame', frame)
                cv2.waitKey(1)
            else:
                log.error(f"[Camera][show_frame]cannot get frame from camera device:{self.__device_index}")

            time.sleep(1 / frame_rate)

    def save_frame(self, save_path: str = './frame.jpg'):
        ret, frame = self.__cap.read()
        if ret:
            cv2.imwrite(save_path, frame)
        else:
            log.error(f"[Camera][get_frame]cannot get frame from camera device:{self.__device_index}")

    @staticmethod
    def cv2_to_image(image) -> PIL.Image.Image:
        image = Image.fromarray(cv2.cvtColor(numpy.asarray(image), cv2.COLOR_RGB2BGR))
        return image


class Timer:
    def __init__(self, config: dict):
        self.__config = config

        if config['name'] == 'boot':
            self.report = BootResult(0.0, 0.0, 0.0)

        elif config['name'] == 'reboot':
            self.report = ReBootResult(0.0, 0.0, 0.0, 0.0)
        else:
            log.error(f"[bootstrap][Timer]this type is not supported: {config['name']}")

    def set_time_report(self, **kwargs):
        self.report = self.report._replace(**kwargs)

    def get_time_report(self) -> BootResult or ReBootResult:
        return self.report


class Observer:
    def __init__(self, config: dict, manual_boot_list: tuple,
                 ip: str = '127.0.0.1', port: int = 2334,
                 camera_device_index: int = 0,
                 target_pics: str = get_current_dir('Test_Data', 'target_pictures')):
        self.__config = config
        self.__manual_boot_list = manual_boot_list

        self.__ip = ip
        self.__client = socket_action.SocketClient(server_ip=ip, server_port=port)

        self.__target_pics = target_pics

        self.__camera = Camera(device_index=camera_device_index)

    def __repr__(self):
        return f"<Observer:{self.__config}\n{self.__manual_boot_list}>"

    def set_env(self, wait_time: int = 60) -> bool:
        status = False

        if self.__config['name'] == 'reboot':
            status = True
            return status

        else:
            msg = {
                'name': self.__config['name'],
                'command': 'SET_ENV',
            }

            try:
                socket_client = socket_action.SocketClient(server_ip=self.__ip, server_port=2333)
                socket_client.send_message(msg)

                time.sleep(wait_time)
                status = True

            except Exception:
                import traceback
                log.error(
                    f"[Observer][set_env]exception is received when sending message to uut:{traceback.format_exc()}")

                status = False

            return status

    def recover_env(self, wait_time: int = 60) -> bool:
        status = False

        if self.__config['name'] == 'boot':
            status = True
            return status

        else:
            msg = {
                'name': self.__config['name'],
                'command': 'RECOVER_ENV',
            }

            try:
                socket_client = socket_action.SocketClient(server_ip=self.__ip, server_port=2334)
                socket_client.send_message(msg)

                time.sleep(wait_time * 1.5)

                if self.__config['os'] == 'wes':
                    man = Man()
                    switch_to_new_user(man)
                    time.sleep(wait_time / 2)

                # close boot_agent of UUT
                socket_client.send_message("REMOTE_CLOSE")
                socket_client = socket_action.SocketClient(server_ip=self.__ip, server_port=2333)
                socket_client.send_message("REMOTE_CLOSE")

                status = True

            except Exception:
                import traceback
                log.error(
                    f"[Observer][recover_env]exception is received when sending message to uut:{traceback.format_exc()}")

                status = False

            return status

    def power_on(self, platform: str,
                 uut_mac: str = 'F8:B4:6A:A1:C8:E7',
                 uut_broadcast: str = '15.83.247.127',
                 uut_port: int = 9, wait_time: int = 30) -> bool:
        status = False

        if platform.upper() in self.__manual_boot_list:
            for i in range(wait_time):
                if i >= wait_time - 5:
                    log.warning(f"[Observer][power_on]please power on the uut manually: [{i + 1}s/{wait_time}s]")
                    time.sleep(1)
                    continue

                log.info(f"[Observer][power_on]wait to power on the uut manually: [{i + 1}s/{wait_time}s]")
                time.sleep(1)

            status = True

        else:
            # try it again 3 times
            for _ in range(3):
                wakeonlan.send_magic_packet(uut_mac, ip_address=uut_broadcast, port=uut_port)

            log.info(
                f"[Observer][power_on]magic packet is sent to uut:"
                f"<mac:{uut_mac},broadcast:{uut_broadcast},port:{uut_port}>")

            status = True

        return status

    def power_off(self) -> bool:
        status = False

        msg = {
            'name': self.__config['name'],
            'command': 'POWER_OFF',
        }

        try:
            self.__client.send_message(msg)

            status = True

        except Exception:
            import traceback
            log.error(
                f"[Observer][power_off]exception is received when sending message to uut:{traceback.format_exc()}")

            status = False

        return status

    def reboot(self) -> bool:
        status = False

        msg = {
            'name': self.__config['name'],
            'command': 'REBOOT',
        }

        try:
            self.__client.send_message(msg)

            status = True

        except Exception:
            import traceback
            log.error(
                f"[Observer][reboot]exception is received when sending message to uut:{traceback.format_exc()}")

            status = False

        return status

    def check_hp_logo(self, wait_time: int = 60, frame_rate: int = 40, threshold: int = 4,
                      save_frame: bool = False) -> bool:
        log.debug(f"[Observer][check_hp_logo]begin to check hp logo")
        status = False
        sum_time = 0

        target_pic = os.path.join(self.__target_pics, self.__config['os'], 'hp_logo.jpg')

        # resolve mt22 wes hp log issue
        if self.__config['platform'].upper() == 'MT22' and self.__config['os'] == 'wes':
            target_pic = os.path.join(self.__target_pics, self.__config['os'], self.__config['platform'], 'hp_logo.jpg')

        log.info(f"[Observer][check_hp_logo]current hp logo image path: {target_pic}")

        time_start = time.time()
        target_pic = Image.open(target_pic)
        target_pic_hash = DHash.calculate_hash(target_pic)

        for i in range(wait_time * frame_rate):
            frame = self.__camera.get_frame()
            if frame is not None:
                image = self.__camera.cv2_to_image(frame)
                image_hash = DHash.calculate_hash(image)
                score = DHash.hamming_distance(image_hash, target_pic_hash)

                log.info(f"[Observer][check_hp_logo]current frame score: {score}")

                if self.__config['os'] == 'linux':
                    threshold = 10

                if score <= threshold:
                    log.info(f"[Observer][check_hp_logo]find a frame and its score is: {score} <= {threshold}")

                    sum_time = time.time() - time_start
                    log.info(f"[Observer][check_hp_logo]sum time of check_hp_logo: {sum_time}s")

                    if save_frame:
                        image.save(get_current_dir('Test_Report', 'check_hp_logo_{}.jpg'.format(time.time())))

                    status = True
                    break
            else:
                log.error(f"[Observer][check_hp_logo]cannot get camera frame from uut")

                status = False
                break

            time.sleep(1 / frame_rate)

        log.debug(f"[Observer][check_hp_logo]end to check hp logo")
        return status

    def check_desktop(self, wait_time: int = 60, frame_rate: int = 20, threshold: int = 1, similarity: float = 0.94,
                      save_frame: bool = False) -> bool:
        log.debug(f"[Observer][check_desktop]begin to check desktop")
        status = False
        sum_time = 0

        target_pic_path = os.path.join(self.__target_pics, self.__config['os'], 'desktop.jpg')
        log.info(f"[Observer][check_desktop]current desktop image path: {target_pic_path}")

        time_start = time.time()
        target_pic = Image.open(target_pic_path)
        target_pic_hash = DHash.calculate_hash(target_pic)

        for i in range(wait_time * frame_rate):
            frame = self.__camera.get_frame()
            if frame is not None:
                if self.__config['os'] == 'wes' or self.__config['os'] == 'linux':
                    image = self.__camera.cv2_to_image(frame)
                    image_hash = DHash.calculate_hash(image)
                    score = DHash.hamming_distance(image_hash, target_pic_hash)

                    log.info(f"[Observer][check_desktop]current frame score: {score}")

                    if self.__config['platform'].upper() == 'MT22':
                        threshold = 2

                    if score <= threshold:
                        log.info(f"[Observer][check_desktop]find a frame and its score is: {score} <= {threshold}")

                        sum_time = time.time() - time_start
                        log.info(f"[Observer][check_desktop]sum time of check_desktop: {sum_time}s")

                        if save_frame:
                            image.save(get_current_dir('Test_Report', 'check_desktop_{}.jpg'.format(time.time())))

                        status = True
                        break

                # elif self.__config['os'] == 'linux':
                #     similarity = 0.84
                #
                #     dst_template = cv2.imread(target_pic_path, 0)
                #     gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                #
                #     result = cv2.matchTemplate(gray_frame, dst_template, cv2.TM_CCOEFF_NORMED)
                #     result = float(numpy.max(result))
                #
                #     log.info(f"[Observer][check_desktop]current similarity of frame is: {result}")
                #
                #     if round(result, 2) >= similarity:
                #         sum_time = time.time() - time_start
                #         log.info(f"[Observer][check_desktop]sum time of check_desktop: {sum_time}s")
                #
                #         if save_frame:
                #             cv2.imwrite(get_current_dir('Test_Report', 'check_desktop_{}.jpg'.format(time.time())),
                #                         frame)
                #
                #         status = True
                #         break

                else:
                    log.error('[Observer][check_desktop]this os type is not supported')
                    break

            else:
                log.error(f"[Observer][check_desktop]cannot get camera frame from uut")

                status = False
                break

            time.sleep(1 / frame_rate)

        log.debug(f"[Observer][check_desktop]end to check desktop")
        return status

    def check_shutdown(self, wait_time: int = 60, frame_rate: int = 20, threshold: int = 3,
                       save_frame: bool = False) -> bool:
        log.debug(f"[Observer][check_shutdown]begin to check shutdown")
        status = False
        sum_time = 0

        time_start = time.time()
        target_pic = os.path.join(self.__target_pics, self.__config['os'], 'shutdown.jpg')
        log.info(f"[Observer][check_shutdown]current shutdown image path: {target_pic}")

        target_pic = Image.open(target_pic)
        target_pic_hash = DHash.calculate_hash(target_pic)

        for i in range(wait_time * frame_rate):
            frame = self.__camera.get_frame()
            if frame is not None:
                image = self.__camera.cv2_to_image(frame)
                image_hash = DHash.calculate_hash(image)
                score = DHash.hamming_distance(image_hash, target_pic_hash)

                log.info(f"[Observer][check_shutdown]current frame score: {score}")

                if score <= threshold:
                    log.info(f"[Observer][check_shutdown]find a frame and its score is: {score} <= {threshold}")

                    sum_time = time.time() - time_start
                    log.info(f"[Observer][check_shutdown]sum time of check_shutdown: {sum_time}s")

                    if save_frame:
                        image.save(get_current_dir('Test_Report', 'check_shutdown_{}.jpg'.format(time.time())))

                    status = True
                    break
            else:
                log.error(f"[Observer][check_shutdown]cannot get camera frame from uut")

                status = False
                break

            time.sleep(1 / frame_rate)

        log.debug(f"[Observer][check_shutdown]begin to check shutdown")
        return status


class Startup:
    def __init__(self, app_name: str = 'boot_agent'):
        self.__app_name = app_name

        if 'window' in platform.platform().lower():
            self.__os = 'win'
        elif 'linux' in platform.platform().lower():
            self.__os = 'linux'
            self.__startup = AddStartup(get_current_dir(app_name))
        else:
            raise OSError(f"This os type is not supported: {self.__os}")

    def add_auto_start(self) -> bool:
        log.debug(f"[Startup][add_auto_start]begin to add auto-start script")

        status = False

        if self.__os == 'win':
            status = self.__add_win_start()
        elif self.__os == 'linux':
            status = self.__add_linux_start()

        log.debug(f"[Startup][add_auto_start]end to add auto-start script")
        return status

    def delete_auto_start(self) -> bool:
        log.debug(f"[Startup][delete_auto_start]begin to add auto-start script")

        status = False

        if self.__os == 'win':
            status = self.__delete_win_start()
        elif self.__os == 'linux':
            status = self.__delete_linux_start()

        log.debug(f"[Startup][delete_auto_start]end to add auto-start script")
        return status

    def is_auto_start(self) -> bool:
        # log.debug(f"[Startup][is_auto_start]begin to add auto-start script")
        status = False

        if self.__os == 'win':
            status, _ = self.__is_win_auto_start()
        elif self.__os == 'linux':
            status = self.__is_linux_auto_start()
        # log.debug(f"[Startup][is_auto_start]end to add auto-start script")

        return status

    def __add_win_start(self,
                        startup_path: str = r'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup') -> bool:

        status = False

        app_path = '{}.exe.lnk'.format(get_current_dir('Test_Utility', self.__app_name))
        log.info(f"[Startup][add_auto_start]current auto-start script path: {app_path}")

        try:
            # lnk = os.path.join(startup_path, self.__app_name + '.exe' + '.lnk')
            #
            # shell = client.Dispatch("WScript.Shell")
            #
            # shortcut = shell.CreateShortCut(lnk)
            # shortcut.TargetPath = app_path
            # shortcut.save()

            if os.path.exists(app_path):
                shutil.copy(app_path, startup_path)

            log.info(f"[Startup][add_auto_start]this auto-start lnk is saved: {startup_path}")

            status = True

        except Exception:
            log.error(
                f"[Startup][add_auto_start]exception is received when adding auto script: {traceback.format_exc()}")

            status = False

        return status

    def __add_linux_start(self) -> bool:
        status = False

        try:
            self.__startup.add_startup()
            status = True
        except Exception:
            log.error(f"[Startup][add_linux_start]cannot add auto-startup script")
            status = False

        return status

    def __delete_win_start(self,
                           startup_path: str = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup') -> bool:
        status = False

        ret, lnk = self.__is_win_auto_start(startup_path=startup_path)
        if ret:
            os.remove(lnk)
            log.info(f"[Startup][delete_auto_start]this lnk is removed: {lnk}")
            status = True
        else:
            status = False

        return status

    def __delete_linux_start(self, dst_auto='/etc/init/auto-run-automation-script.conf',
                             wait_time: float = 0.5) -> bool:
        status = False

        if os.path.exists(dst_auto):
            os.remove(dst_auto)
            time.sleep(wait_time)

            if os.path.exists(dst_auto):
                status = False
            else:
                status = True
        else:
            status = True

        return status

    def __is_win_auto_start(self,
                            startup_path: str = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup') -> (
            bool, str or None):
        status = False
        lnk_path = None

        lnk = os.path.join(startup_path, self.__app_name + '.exe' + '.lnk')
        if os.path.exists(lnk) and os.path.isfile(lnk):
            log.info(f"[Startup][is_win_auto_start]this auto-script lnk exists: {lnk}")
            status = True
            lnk_path = lnk
        else:
            log.error(f"[Startup][is_win_auto_start]this auto-script lnk not exists: {lnk}")
            status = False
            lnk_path = None

        return status, lnk_path

    def __is_linux_auto_start(self, dst_auto='/etc/init/auto-run-automation-script.conf') -> bool:
        status = False

        if os.path.exists(dst_auto):
            status = True
        else:
            status = False

        return status


class BaseBootTest(metaclass=ABCMeta):
    def __init__(self, config: dict, platform: str, boot_wait_time: int = 120,
                 camera_device_index: int = 0,
                 manual_boot_list: tuple = ('MT32', 'MT46')):
        self.__config = config

        self.__platform = platform
        self.__boot_wait_time = boot_wait_time
        self.__manual_boot_list = manual_boot_list

        self.__observer = Observer(config, manual_boot_list=self.manual_boot_list,
                                   ip=config['client_ip'],
                                   camera_device_index=camera_device_index)
        self.__timer = Timer(config)

    @property
    def config(self) -> dict:
        return self.__config

    @property
    def platform(self) -> str:
        return self.__platform

    @property
    def manual_boot_list(self) -> tuple:
        return self.__manual_boot_list

    @property
    def boot_wait_time(self) -> int:
        return self.__boot_wait_time

    @property
    def observer(self):
        return self.__observer

    @property
    def timer(self):
        return self.__timer

    def set_env(self) -> bool:
        log.debug("[BootTest][set_env]the set_env process is started")

        self.observer.set_env()

        log.debug("[BootTest][set_env]the set_env process is ended")

        return True

    def recover_env(self) -> bool:
        log.debug("[BootTest][recover_env]the recover_env process is started")

        self.observer.recover_env()

        log.debug("[BootTest][recover_env]the recover_env process is ended")

        return True

    @abstractmethod
    def test_result(self) -> typing.List:
        pass

    @abstractmethod
    def analyse_result(self, results: typing.Any) -> typing.Any:
        pass

    @abstractmethod
    def write_result(self, results: typing.Any) -> typing.Any:
        pass

    def __repr__(self):
        return f"<BootTest:" \
               f"{self.platform},{self.boot_wait_time},{self.manual_boot_list}>" \
               f"{self.observer},{self.timer}"

    def __str__(self):
        return self.__repr__()

    def __del__(self):
        pass

    def __enter__(self):
        if self.set_env():
            return self
        else:
            raise RuntimeError(f'[BootTest][enter]the set_env process is failed')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.recover_env():
            # self.__del__( )
            client = socket_action.SocketClient(server_ip='127.0.0.1', server_port=6667)
            client.send_message('TEST FINISHED')
        else:
            raise RuntimeError(f'[BootTest][exit]the recover_env process is failed')


class BaseControlled(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def set_env(self) -> bool:
        pass

    @abstractmethod
    def recover_env(self) -> bool:
        pass

    @abstractmethod
    def power_on(self, wait_time: int = 120) -> bool:
        pass

    @abstractmethod
    def power_off(self, wait_time: int = 120) -> bool:
        pass

    @abstractmethod
    def reboot(self, wait_time: int = 120) -> bool:
        pass


class WesControlled(BaseControlled):
    def __init__(self, boot_type: str = 'boot', agent_name: str = 'boot_agent'):
        super(WesControlled, self).__init__()

        self.__boot_type = boot_type
        self.__startup = Startup(app_name=agent_name)

    def set_env(self) -> bool:
        log.debug("[WesControlled][set_env]the set_env process is started")

        if not self.__startup.is_auto_start():
            self.__startup.add_auto_start()
            if self.__startup.is_auto_start():
                log.info(f"[WesControlled][set_env]this socket agent is added successfully")
                if self.__boot_type == 'boot':
                    self.power_off()
            else:
                log.error(f"[WesControlled][set_env]this socket agent is added unsuccessfully")
        else:
            log.info(f"[WesControlled][set_env]this socket agent was added to auto-startup")
            if self.__boot_type == 'boot':
                self.power_off()

        log.debug("[WesControlled][set_env]the set_env process is ended")

    def recover_env(self) -> bool:
        log.debug("[WesControlled][recover_env]the recover_env process is started")

        if self.__startup.is_auto_start():
            self.__startup.delete_auto_start()
            if not self.__startup.is_auto_start():
                log.info(f"[WesControlled][recover_env]boot socket agent is deleted from auto-startup successfully")
            else:
                log.error(f"[WesControlled][recover_env]boot socket agent is deleted from auto-startup unsuccessfully")
        else:
            log.info(f"[WesControlled][recover_env]boot socket agent was deleted from auto-startup")

        log.debug("[WesControlled][recover_env]the recover_env process is ended")

    def power_on(self, wait_time: int = 0):
        log.debug("[WesControlled][power_on]the power_on process is started")

        log.debug("[WesControlled][power_on]the power_on process is ended")

    def power_off(self, wait_time: int = 0):
        log.debug("[WesControlled][power_off]the power_off process is started")

        cmd = "shutdown /s /t {}".format(wait_time)
        log.info(f"[WesControlled][power_off]this command will be executed rapidly: {cmd}")
        os.system(cmd)

        # log.debug("[WesControlled][power_off]the power_off process is ended")

    def reboot(self, wait_time: int = 0):
        log.debug("[WesControlled][reboot]the reboot process is started")

        cmd = "shutdown /r /t {}".format(wait_time)
        log.info(f"[WesControlled][reboot]this command will be executed rapidly: {cmd}")
        os.system(cmd)

        # log.debug("[WesControlled][reboot]the reboot process is ended")

    def __exec_main_agent(self):
        log.debug("[WesControlled][exec_main_agent]the exec_main_agent process is started")

        if not is_admin():
            log.info(f"[WesControlled][exec_main_agent]current user permission is User")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        else:
            log.info(f"[WesControlled][exec_main_agent]current user permission is Admin")
            os.system(get_current_dir("run.exe") + " /agent")

        log.debug("[WesControlled][exec_main_agent]the exec_main_agent process is ended")


class LinuxControlled(BaseControlled):
    def __init__(self, boot_type: str = 'boot', agent_name: str = 'boot_agent'):
        super(LinuxControlled, self).__init__()

        self.__boot_type = boot_type
        self.__startup = Startup(app_name=agent_name)

    def set_env(self, service_name: str = 'auto') -> bool:
        log.debug("[LinuxControlled][set_env]the set_env process is started")

        if not self.__startup.is_auto_start():
            self.__startup.add_auto_start()
            if self.__startup.is_auto_start():
                log.info(f"[LinuxControlled][set_env]this socket agent is added successfully")

                status = subprocess.getoutput(f"systemctl enable {service_name}").strip()
                log.info(f"[LinuxControlled][set_env]current status after enable it: {status}")

                status = subprocess.getoutput(f"systemctl start {service_name}").strip()
                log.info(f"[LinuxControlled][set_env]current status after start it: {status}")

                log.debug("[LinuxControlled][set_env]the set_env process is ended")

                if self.__boot_type == 'boot':
                    self.power_off()
            else:
                log.error(f"[LinuxControlled][set_env]this socket agent is added unsuccessfully")
        else:
            log.info(f"[LinuxControlled][set_env]this socket agent was added to auto-startup")

            status = subprocess.getoutput(f"systemctl enable {service_name}").strip()
            log.info(f"[LinuxControlled][set_env]current status after enable it: {status}")

            status = subprocess.getoutput(f"systemctl start {service_name}").strip()
            log.info(f"[LinuxControlled][set_env]current status after start it: {status}")

            log.debug("[LinuxControlled][set_env]the set_env process is ended")

            if self.__boot_type == 'boot':
                self.power_off()

    def recover_env(self, service_name: str = 'auto',
                    conf_path: str = '/etc/init/auto-run-automation-script.conf') -> bool:
        log.debug("[LinuxControlled][recover_env]the recover_env process is started")

        status = subprocess.getoutput(f'systemctl is-enabled {service_name}').strip()
        log.info(f"[LinuxControlled][recover_env]current status of auto.service is: {status}")

        if status == 'enabled':
            res = subprocess.getoutput(f'systemctl disable {service_name}')
            log.info(f"[LinuxControlled][recover_env]current status after disable it: {res}")

        if os.path.exists(conf_path):
            os.remove(conf_path)
            log.info(f"[LinuxControlled][recover_env]removed successfully from system: {conf_path}")

        startup = Startup(app_name='run')
        startup.add_auto_start()
        status = subprocess.getoutput(f"systemctl enable {service_name}")

        log.info(f"[LinuxControlled][recover_env]current status after enable it:{status}")
        log.debug("[LinuxControlled][recover_env]the recover_env process is ended")

        self.reboot()

    def power_on(self, wait_time: int = 0):
        log.debug("[LinuxControlled][power_on]the power_on process is started")

        pass

        log.debug("[LinuxControlled][power_on]the power_on process is ended")

    def power_off(self, wait_time: int = 0):
        log.debug("[LinuxControlled][power_off]the power_off process is started")

        cmd = "poweroff --poweroff"
        log.info(f"[LinuxControlled][power_off]this command will be executed rapidly: {cmd}")
        os.system(cmd)

        # log.debug("[LinuxControlled][power_off]the power_off process is ended")

    def reboot(self, wait_time: int = 0):
        log.debug("[LinuxControlled][reboot]the reboot process is started")

        cmd = "poweroff --reboot"
        log.info(f"[LinuxControlled][reboot]this command will be executed rapidly: {cmd}")
        os.system(cmd)

        # log.debug("[LinuxControlled][reboot]the reboot process is ended")


def start(message: dict):
    log.debug(f"[bootstrap][start]current message is: {message}")

    if 'window' in platform.platform().lower():
        controlled = WesControlled(boot_type=message['name'])
    else:
        controlled = LinuxControlled(boot_type=message['name'])

    if message['command'].upper() == 'SET_ENV':
        controlled.set_env()

    elif message['command'].upper() == 'RECOVER_ENV':
        controlled.recover_env()

    elif message['command'].upper() == 'POWER_OFF':
        controlled.power_off()

    elif message['command'].upper() == 'REBOOT':
        controlled.reboot()

    else:
        log.error(f"[bootstrap][start]this message is not supported: {message}")
