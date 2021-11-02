import datetime
import os
import platform
import subprocess
import time

from Common.common import WriteFilter, BCUConfig, HpThinUpdatePanel
from Common.common import get_element, OSTool
from Common.log import log


class uut_operator():

    def __init__(self):
        self.write_filter = WriteFilter()
        self.thinupdate = HpThinUpdatePanel()

    def uut_reboot(self, t):
        """
        uut control reboot
        :return:
        """
        # t: wait time after sleep
        log.info('Start rebooting.')
        subprocess.Popen('shutdown -r -t 1')
        time.sleep(t)

    def check_write_filter_status(self):
        status = self.write_filter.check_state_ui()
        log.info(f'[uut_operator][check_write_filter_status] value {status}')
        if status != 'DISABLE':
            log.info('[uut_operator][check_write_filter_status] write filter result is expected')
            return True
        else:
            log.info('[uut_operator][check_write_filter_status] write filter result is not expected')
            return False

    def uut_open_thinupdate_capture(self, check_cycle: int = 10, wait_time: int = 6):
        if not self.thinupdate.open_panel():
            log.info('[uut_operator][uut_open_thinupdate_capture] thinupdate open fail')
            return False
        else:
            for i in range(check_cycle):
                capture_image_btn = get_element('CAPTURE_STATUS')
                capture_btn = get_element('CAPTURE_BUTTON')
                if capture_image_btn.Exists():
                    capture_image_btn.Click()
                    if capture_btn.Exists():
                        capture_btn.Click()
                        capture_start_path = OSTool.get_current_dir("Test_Report", 'capture_start.txt')
                        with open(capture_start_path, 'r') as record:
                            start_time = datetime.datetime.now()
                            record.write('{}'.format(start_time))
                        return True
                else:
                    time.sleep(wait_time)
                    continue
            log.error(
                f'[uut_operator][uut_open_thinupdate_capture] found cpature_image time out{check_cycle * wait_time}')
            return False

    def uut_edit_u_disk_position(self):
        """
        to slove mtc not enter F9 problem
        check u disk position is first before deploy
        if not edit u disk
        else: return True
        platform: DTC OR MTC
        :return:
        """
        bcu_tool_path = OSTool.get_current_dir('Test_Utility', 'BiosConfigUtility64.exe')
        bcu_setting_file = OSTool.get_current_dir('Test_Data', 'td_thinupdate', 'bios.txt')
        os.system("{} /get:{}".format(bcu_tool_path, bcu_setting_file))
        for i in range(10):
            if os.path.exists(bcu_setting_file):
                break
            else:
                time.sleep(1)
        else:
            raise FileNotFoundError('No {} file'.format(bcu_setting_file))
        bcu = BCUConfig(bcu_setting_file)
        platform_name = platform.platform()
        if 'T' in platform_name.upper():
            log.info('[uut_operator][uut_edit_u_disk_position] this is MTC')
            bcu_boot_order = bcu.config.get('UEFI Boot Order')
            mtc_list = ['HDD:SATA:1', 'HDD:M.2:1']
            if bcu_boot_order[0] == 'HDD:USB:1' and bcu_boot_order[1] in mtc_list:
                log.info(f'[uut_operator][uut_edit_u_disk_position] bcu boot order value:{bcu_boot_order[0]}')
                return True
            else:
                bcu.reorder('UEFI Boot Order', 'HDD:USB:1', 1)
                bcu.reorder(('UEFI Boot Order', bcu_boot_order[0], 2))
                return
        else:
            log.info('[uut_operator][uut_edit_u_disk_position] this is DTC')
            bcu_boot_sources = bcu.config.get('UEFI Boot Sources')
            if bcu_boot_sources[0] == 'USB Hard Drive' and bcu_boot_sources[1] == 'Windows Boot Manager':
                return True
            else:
                log.info(f'[uut_operator][uut_edit_u_disk_position] current boot source value:{bcu_boot_sources[0]}')
                bcu.reorder('UEFI Boot Sources', 'USB Hard Drive', 1)
                bcu.reorder('UEFI Boot Sources', 'Windows Boot Manager', 2)
                return

    def uut_enable_wirte_filter_cmd(self):
        """
        reboot after capture we should enable write filter
        enable write filter we should reboot to make effort
        :return:
        """
        self.write_filter.enable_hpwf_cmd()
