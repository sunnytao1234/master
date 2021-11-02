import traceback

import cv2
import numpy

from Common import Kernel_ERROR, Organ_HAND_MagicKey, Organ_EYE_Camera, Organ_HAND_STM32
from Common.common import SendKey
from Common.common_function import *

interval_1 = 0.3
interval_2 = 1
interval_3 = 3
threshold = 0.95


class ManCFG:
    def __init__(self, man_site):
        """
        instantiated camera/magic key/video card
        :param man_site:
        """
        self.log = log
        yaml_path = get_current_dir('Test_Data', 'man_config.yml')
        with open(yaml_path) as F:
            config_dict = yaml.safe_load(F)
            print(config_dict)
        try:
            self.MV = config_dict[man_site]
        except KeyError:
            raise Kernel_ERROR.ManSiteError()

    def magic_key(self):
        if self.MV[1][0] == 'MagicKey':
            try:
                return Organ_HAND_MagicKey.Magic(self.MV[1][1])
            except Exception:
                raise Kernel_ERROR.MagicKeyNotExistError()
        elif self.MV[1][0] == 'Null':
            return None
        else:
            return None

    def stm32_key(self):
        if self.MV[1][2] == 'STM32':
            try:
                return Organ_HAND_STM32.Hand(self.MV[1][3])
            except Exception:
                raise Kernel_ERROR.STM32NotExistError()
        elif self.MV[1][2] == 'Null':
            return None
        else:
            return None

    def camera(self):
        if self.MV[0][0] in ['EYE_Camera']:
            try:
                return Organ_EYE_Camera.Eye(self.MV[0][1])
            except Exception:
                raise Kernel_ERROR.EyeNotExistError()
        # elif self.MV[0][0] in ['Video_Capture_Card']:
        #     try:
        #         obj = Organ_Video_Card.QWindow
        #         return obj
        #     except Exception:
        #         raise Kernel_ERROR.EyeNotExistError()
        elif self.MV[0][0] == 'EYE_Null':
            return None
        else:
            return None


class Man:
    def __init__(self, site='1'):
        """
        Encapsulation of Key and camera
        hand: magic key
        hand_aid: stm32 key
        :param site:
        """
        self.log = log
        self.mc = ManCFG(site)
        self.magic_key = self.mc.magic_key()
        self.smt32_key = self.mc.stm32_key()
        self.eye = self.mc.camera()
        self.site = site
        self.valve_instance = None

    def __get_view(self):
        return self.eye.snap_shot()

    def __judge(self, png, confidence, times=20):
        """
        check if png similarity match the confidence
        :param png: <class 'str'>picture file name
        :param confidence: <class 'float'> threshold value of similarity
        :return:
        """
        sample = self.__get_view()
        for i in range(times):
            if os.path.exists(sample):
                break
            else:
                sample = self.__get_view()
                time.sleep(1)
        else:
            log.info('{} is not Found in {}s'.format(sample, times))
            return False
        try:
            res = self.get_similarity(sample, png)
            log.info('similarity: {}'.format(float(res)))
        except Exception:
            self.log.error(traceback.format_exc())
            return
        if float(res) >= confidence:
            log.info('[!] Target Screen Found : ' + str(png) + ' @ ' + str(res))
            log.info('    ...............remove snapshot.....................')
            os.remove(sample)
            t_flag = True
        else:
            t_flag = False
        return t_flag

    def __push_key(self, kn, hand_type='HAND', t=interval_1):
        # hand: magic key
        # hand_aid: smt32 key
        if hand_type == 'HAND':
            self.magic_key.key(kn, t)
        elif hand_type == 'HAND_AID':
            self.smt32_key.key(kn, t)

    def press_key(self, key_name, n=1, hand_type='HAND'):
        """
        :param key_name:
        :param n: count
        :param hand_type
        :return:
        """
        for i in range(n):
            self.log.info('Push The Key : [' + str(key_name) + ']')
            self.__push_key(key_name, hand_type)

    def press_key_delay(self, key_name, t=interval_3, hand_type='HAND'):
        # delay several seconds after press a key
        self.log.info('Push The Key : [{}] and Delay {}'.format(str(key_name), t))
        self.__push_key(key_name, hand_type)
        self.wait(t)

    def press_key_list(self, key_list, t=interval_2, hand_type='HAND'):
        for key_name in key_list:
            self.log.info('Push The Key : [' + str(key_name) + ']')
            self.__push_key(key_name, hand_type)
            self.wait(t)

    def input_string(self, string, hand_type='HAND'):
        self.log.info('Enter The Text : [' + string + ']')
        for i in string:
            self.__push_key(i, hand_type)

    def wait(self, t):
        self.log.info('wait {} second'.format(t))
        time.sleep(t)

    @staticmethod
    def get_similarity(sample, template):
        time.sleep(0.5)
        src = cv2.imread(sample, 0)
        # img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dst = cv2.imread(template, 0)
        log.info('video source: {}'.format(src.shape))
        log.info('template: {}'.format(dst.shape))
        res_matrix = cv2.matchTemplate(src, dst, cv2.TM_CCOEFF_NORMED)
        res = numpy.max(res_matrix)
        return float(res)

    def wait_screen(self, t, png, confidence=threshold):
        log.info('Waiting : ' + str(png))
        t_flag = False
        start_time = time.time()
        while time.time() - start_time <= t:
            if self.__judge(png, confidence):
                t_flag = True
                break
        return t_flag

    def wait_screens(self, t, target, confidence=threshold):
        """
        check if the video image match one of the png_list in a given time
        :param t: <class 'int'> a given time
        :param target: picture list or picture folder path
        :param confidence: <class 'float'> threshold of similarity
        :return: <class 'bool'>
        """
        t_flag = False
        start_time = time.time()
        while time.time() - start_time <= t:
            if isinstance(target, list):
                target_list = target
            elif all([isinstance(target, str), os.path.isabs(target)]):
                target_list = []
                file_list = os.listdir(target)
                for file in file_list:
                    target_list.append(os.path.join(target, file))
            else:
                raise TypeError("parameter 'target' only support list or absolute path")
            log.info('Waiting : ' + str(target_list))
            for png in target_list:
                if self.__judge(png, confidence):
                    t_flag = True
                    self.wait(10)
                    break  # skip the rest pictures
            if t_flag:
                break
        if not t_flag:
            log.info('No Target Screen Found')
        return t_flag

    def do_until_plus(self, t, kn, target, confidence=threshold, hand_type='HAND'):
        """
        keep pressing a key until the video image match one of the png_list
        :param t: <class 'int'> a given time
        :param kn: key name
        :param target: picture list or picture folder path
        :param confidence: <class 'float'> threshold of similarity
        :param hand_type:
        :return:
        """
        # log.info('Waiting : ' + str(png_list))
        if hand_type == 'HAND':
            sk = SendKey(self.magic_key, interval_1)
        elif hand_type == 'HAND_AID':
            sk = SendKey(self.smt32_key, interval_1)
        else:
            return
        sk.kn = kn  # set what key will be pressed
        sk.setDaemon(True)
        sk.start()
        self.wait(5)
        t_flag = self.wait_screens(t, target, confidence, )
        sk.stop()
        return t_flag

    def do_until(self, kn, t=5, hand_type='HAND') -> None:
        if hand_type == 'HAND':
            sk = SendKey(self.magic_key, interval_1)
        elif hand_type == 'HAND_AID':
            sk = SendKey(self.smt32_key, interval_1)
        else:
            return
        sk.kn = kn  # set what key will be pressed
        sk.setDaemon(True)
        sk.start()
        self.wait(t)
        sk.stop()
        return
