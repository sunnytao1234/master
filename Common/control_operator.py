import os
import shutil
import time
from datetime import datetime

from Common.Organ_Video_Card import SnapshotJPG
from Common.common import OSTool
from Common.log import log
from Common.recognizer import recognize_string


class control_operator():
    def __init__(self, Man, wes=True):
        self.man = Man()
        self.wes = wes
        self.snap = SnapshotJPG()

    def recode_capture_start_time(self, loop: int = 0):
        """
        control run
        check logo appear
        write time on control txt
        :return:
        """
        start_time = datetime.now()
        start_txt_path = OSTool.get_current_dir("Test_Report", 'capture_start.txt')
        new_name = OSTool.get_current_dir("Test_Report", "capture_start{}.txt".format(loop))
        if os.path.exists(start_txt_path):
            os.rename(start_txt_path, new_name)
        with open(start_txt_path, 'w') as recode:
            recode.write('{}'.format(start_time))
        return start_time

    def recode_capture_end_time(self, loop: int = 0):
        """
        control run
        check logo appear
        write time on control txt
        :return:
        """
        end_time = datetime.now()
        start_txt_path = OSTool.get_current_dir("Test_Report", 'capture_ended.txt')
        new_name = OSTool.get_current_dir("Test_Report", "capture_ended{}.txt".format(loop))
        if os.path.exists(start_txt_path):
            os.rename(start_txt_path, new_name)
        with open(start_txt_path, 'w') as recode:
            recode.write('{}'.format(end_time))
        return end_time

    def calculate_time(start_time=recode_capture_start_time, end_time=recode_capture_end_time):
        calculate_time_value = str((end_time - start_time)).strip().split('.')[0]
        log.info(f'[calculate_time]calculate_time_value:{calculate_time_value}')
        calculate_time_value_list = calculate_time_value.split(':')
        log.info(f'[calculate_time]calculate_time_value_list:{calculate_time_value_list}')
        if int(calculate_time_value_list[0]) == 0:
            str_value = ':'
            time_value = str_value.join((calculate_time_value_list[1], calculate_time_value_list[2]))
        else:
            time_value = calculate_time_value

        log.info(f'[calculate_time] time value {time_value} ')

        return time_value

    def check_usb_no_sign(self):
        """
        control run
        :return:
        """
        pass

    def main_capture_process(self, check_cycle: int = 3600, wait_time: int = 1):
        """control run"""
        for i in range(check_cycle):
            self.snap.snapshot()
            capture_picture_path = self.snap.view()
            if '100%' in recognize_string(capture_picture_path, lang='eng'):
                log.info('[control_operator][main_capture_process] capture is complete')
                with open('capture_end.txt', 'w') as f:
                    f.write(time.time())
                return True
        pass

    def check_capture_result(self):
        """
        control run
        :return:
        """

    def reboot_enter_os(self, t):
        """"""
        os.system('shutdown -r t 1')
        time.sleep(t)
        pass

    def swithch_admin(self):
        """
        uut run
        :return:
        """
        self.man.press_key_delay('win', 1)
        self.man.press_key_delay('{ctrl}{alt}{del}', 3)
        self.man.press_key_delay('Down', 1)
        self.man.press_key('Enter')
        return True

    def exit_winxp_capture_fail(self, check_cycle: int = 30, wait_time: int = 1):
        """
        control run
        :return:
        """
        for i in range(check_cycle):
            self.snap.snapshot()
            start_capture_path = self.snap.view()
            capture_winxp = OSTool.get_current_dir('Test_Data', 'td_thinupdate', 'capture', 'enter_winxp', '1.jpg')
            if '' in recognize_string(start_capture_path, lang='eng'):
                log.info('[control_operator][exit_winxp_capture_fail] check capture enterning winxp')
                shutil.copy(start_capture_path, capture_winxp)
                return True
            else:
                if os.path.exists(start_capture_path):
                    os.remove(start_capture_path)
                time.sleep(wait_time)
                continue

    def recover_env(self):
        """:
        control run
        if capture appear error,
        you need recover env
        """
        self.man.input_string('exit')
        self.man.wait(1)
        self.man.press_key('Enter')

    def control_deploy_result(self, check_cycle: int = 1800, wait_time: int = 1):
        for i in range(check_cycle):
            deploy_screen = self.snap.snapshot()  # 截图
            deploy_screen_path = self.snap.view()
            if 'successful' in recognize_string(deploy_screen_path, lang='eng'):
                log.info('[control_opearator][control_deploy_result] deploy process is complete')
                return True
            elif 'error' in recognize_string(deploy_screen_path, lang='eng'):
                log.info('[control_opearator][control_deploy_result] deploy process have some not recover error')
                return False
            else:
                if os.path.exists(deploy_screen_path):
                    os.remove(deploy_screen_path)
                    time.sleep(wait_time)
                    continue

    def control_deploy_main_process(self):
        time.sleep(60)
        self.man.input_string("Y")
        self.man.wait(2)
        self.man.input_string("Y")
        if self.control_deploy_result():
            log.info('[control_operator][control_deploy_main_process] deploy successful we will press s to'
                     ' shutdown uut')
            self.man.input_string("S")
            self.man.wait(60)
            self.man.valve_instance.close()
            self.man.valve_instance.close()
            self.man.wait(5)
            return True
        else:
            log.error('[control_operator][control_deploy_main_process] deploy process appear error,we not restore env')
            return False
