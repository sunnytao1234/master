from Common.log import log
import subprocess
import time
import os
from Test_Script.base.common import WriteFilter, HpThinUpdatePanel
from Test_Script.base.common import get_element, OSTool, read_function_tool_yaml
import shutil

class uut_operator:

    agent_path = OSTool.get_current_dir('Test_Utility','agent.bat')
    start_up_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp'

    def __init__(self):
        self.write_filter = WriteFilter()
        self.thinupdate = HpThinUpdatePanel()

    def uut_reboot(self,t=1):
        """
        uut control reboot
        :return:
        """
        # t: wait time after sleep
        log.info('Start rebooting.')
        subprocess.Popen('shutdown -r -t 1')
        time.sleep(t)

    def close_write_filter(self):
        self.write_filter.close_panel()

    def set_uut_env(self):
        # logo_on_admin()
        if not os.path.exists(self.start_up_path):
            return False
        new_path = self.start_up_path + '\\' +'agent.bat'
        if not os.path.exists(new_path):
            log.info('[uut_operator][logo_admin_and_agent_add_startup] windows start up not found agent.exe')
            shutil.copy(self.agent_path,new_path)
        pass


    def install_docket(self,platform):
        platform_list = read_function_tool_yaml()
        log.info('[uut_operator][install_docker] platfrom list value:{}'.format(platform_list))
        if platform in platform_list:
            docket_packet_path = OSTool.get_current_dir('Test_Utility','sp110277_LAN.exe')
            docket_path = r'C:\SWSetup\SP110277\FAILURE.FLG'
            subprocess.Popen('{} /s'.format(docket_packet_path))
            if os.path.exists(docket_path):
                log.info('[uut_control][install_docket] install docket successful')
                return True
        else:
            log.info('[uut_operator][install_docket]not need install docket')
            return True

    def check_write_filter_status(self):
        status =self.write_filter.check_state()
        log.info(f'[uut_operator][check_write_filter_status] value {status}')
        if status == 'DISABLED':
            log.info('[uut_operator][check_write_filter_status] write filter result is expected')
            return True
        else:
            log.info('[uut_operator][check_write_filter_status] write filter result is not expected')
            return False


    def start_capture(self, check_cycle: int = 10, wait_time: int = 6):
        if not self.thinupdate.open_panel():
            log.info('[uut_operator][uut_open_thinupdate_capture] thinupdate open fail')
            return False
        else:

            for i in range(check_cycle):
                capture_image_btn = get_element('CAPTURE_IMAGE')
                capture_btn = get_element('IMAGE_CAPTURE')
                yes_btn = get_element('ThINUPDATE_YES')
                warn_window = get_element('ThINUPDATE_WARNING')
                error_btn = get_element('THIN_ERROR_DIALOG')
                ok_btn = get_element('ThINUPDATE_OK')
                if capture_image_btn.Exists():
                    capture_image_btn.Click()
                if error_btn.Exists():
                    ok_btn.Click()
                    if capture_btn.Exists():
                        capture_image_btn.Click()
                        if warn_window.Exists():
                            yes_btn.Click()
                    return True
                if capture_btn.Exists():
                    capture_btn.Click()
                if warn_window.Exists():
                    yes_btn.Click()
                    return True
                else:
                    time.sleep(wait_time)
                    continue
            log.error(f'[uut_operator][uut_open_thinupdate_capture] found cpature_image time out{check_cycle*wait_time}')
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
        log.info('[uut_operator][u_disk] start u disk')
        value = subprocess.run('C:\Windows\sysnative\BootOrder.exe')
        time.sleep(5)
        log.info('[uut_operator][u_disk] value:{}'.format(value))

    def uut_disable_wirte_filter_cmd(self):
        """
        reboot after capture we should enable write filter
        enable write filter we should reboot to make effort
        :return:
        """
        self.write_filter.disable_hpwf_cmd()




