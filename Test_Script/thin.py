import time
from Common.common_function import OSTool
from Common.exception import IncorrectOS
from Common.log import log
from Test_Script.base.uut_operator import uut_operator
from Common.tc_info import WESInfo
from Test_Script.base import socket_action
from Test_Script.base.common import get_server_ip, disable_uac

class Thinupdate:
    def __init__(self):
        """capture test for wes"""
        self.__test_data = None
        self.uut = uut_operator()
        self.wes = WESInfo()
        self.client = socket_action.SocketClient(server_ip='{}'.format(get_server_ip().strip()), server_port=55555)
        self.save_path = OSTool.get_current_dir('result.xlsx')
        self.template_path = OSTool.get_current_dir('Test_Data','excle_template.xlsx')
        self.data_start_col = 8
        self.data_start_row = 2
        """
        {name: 'storage', loop: 3, os: wes, platform: mt31, tester: balance@hp.com, 
        os_info: windows10-xx-xxx, platform_info: hp mt31, ml_info: xxxxx, memory_info: xxxx8G,
        disk_info: sumsun xxxxx32G, disk_pn: 12345, bios_info: xxxx, cpu_info: xxxx@2.0GHz,
        gpu_info: xxxx, main_board_info: 321a}
        """

    def thinupdate_control_env(self):
        log.info('[Thinupdate][open_udisk] bengin start open u disk')
        self.client.send_message(msg='open disk')


    def thinupdate_prepare_env(self):
        """
        logo on admin and add agent.exe to windows startup
        :return:
        """

        self.uut.set_uut_env()
        log.info(f'platform value {self.platform}')
        self.uut.install_docket(platform=self.platform)

    def check_write_filter_status(self):
        """
        use cmd to check status
        """
        status = self.uut.check_write_filter_status()
        if status:
            log.info('[thin][check_write_filter_status] write filter status is  disable')
        else:
            self.uut.uut_disable_wirte_filter_cmd()
            self.thin_uut_reboot()
        self.thinupdate_control_env()


    def thin_uut_reboot(self):
        self.client.send_message(msg='uut reboot')
        time.sleep(5)
        self.uut.uut_reboot(t=1)


    def open_thinupdate_click_capture(self):
        """
        launch diskmark
        :return:
        """
        self.uut.start_capture()
        return True

    def set_config(self, value: dict, **kwargs):
        self.__test_data = value
        self.mac = value.get('mac_info')
        self.loop = value.get('loop')
        self.size = value.get('memory_info')
        log.info('SIZE VALUE:{}'.format(self.size))
        self.platform = value.get('platform_info')
        self.os_value = value.get('os_info')
        self.ml_info = value.get('ml_info')
        self.vendor = value.get('memory_info')
        self.save_path = OSTool.get_current_dir('Test_Report',
                                                'Thin_capture_{a}_{b}.xlsx'.format(a=self.platform, b=self.os_value))

    def recode_capture_start_time(self):
        log.info('[thin][recode_capture_start_time] begin recode start time')
        self.client.send_message(msg='recode capture start')


    def check_capture_deploy_status(self):
        """a
        get diskmark test sttus
        :return: status of diskmark
        """
        self.client.send_message(msg='check capture status')


    def test_capture2_1(self):
        self.uut.uut_disable_wirte_filter_cmd()
        self.uut.uut_reboot()

    def test_capture2_2(self):
        self.uut.start_capture()


    def test_deploy(self):
        self.uut.uut_disable_wirte_filter_cmd()
        disable_uac()
        self.uut.uut_reboot()

    def test_deploy2(self):
        self.uut.uut_edit_u_disk_position()
        self.uut.uut_reboot(t=1)


    def test_thinupdate(self):
        log.info('[thin][test_capture] bengin test_thinupdate')
        self.thinupdate_prepare_env()
        self.check_write_filter_status()
        click_capture = self.uut.start_capture()
        if not click_capture:
            return False
        self.recode_capture_start_time()
        self.check_capture_deploy_status()



    def open_u_disk(self):
        self.client.send_message('open disk')


    def collect_thin_result(self):
       self.client.send_message('collect_result')


    def test_thin(self):
        """
        run using specific config
        :return:
        """
        for loop in range(3):
            log.info(f'[Thinupdate][test_thinupdate] begin {loop+1} thinupdate')
            self.test_thinupdate()
            log.info(f'[Thinupdate][test_thinupdate] Run {loop+1} thinupdate Finished')
            return True




def start(value: dict,**kwargs):
    """
    main function for reboot test
    1. support cross platform
    2. support all reboot test items
    3. collect result and analyze test result
       3.1 get result
       3.2 get average result
       3.3 mark abnormal data as red in excel
    4. write to excel as expected format
    5. all exception should be covered
    :param _os: thinpro7x wes10_rsx
    :param loop: test loop
    :param kwargs:
    :return: None
    """
    try:
        log.info('value:{}'.format(value))
        if value.get('os') == 'wes':
            thin = Thinupdate()
        else:
            log.error('[Thinupdate][start]not support linux')
            raise IncorrectOS('Incorrect OS given')
        thin.set_config(value)
        print(thin.set_config(value))
        thin.test_thin()
    except:
        import traceback
        log.error(f'[Thinupdate][start]get exception during test Thinupdate:{traceback.format_exc()}')
        traceback.print_exc()

    finally:
        log.info("[Thinupdate][start]end to test thinupdate case")

    return None
