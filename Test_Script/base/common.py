import copy
import ctypes
import hashlib
import ipaddress
import locale
import os
import os.path
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
import traceback

import psutil
import serial.tools.list_ports
from PIL import Image, ImageOps

from Common import file_transfer, registry_operator
from Common.common_function import OSTool, OS
from Common.file_operator import TxtOperator, YamlOperator
from Common.registry_operator import RegistryTools
from Test_Script.base import ocr_client

if 'window' in platform.platform().lower():
    from Common.ui_automation import getElementByType
    import uiautomation as ui
    from win32com.client import GetObject
    import win32api
    import win32con

from Common.common import get_current_dir
from Common.log import log

REQUIRED_ITEMS = {
    'Test_Data': {
        'camera/camera_default.yml': {
            'wes': '',
            'linux': ''
        },

        'excle/win10_mark.yaml': {
            'wes': '',
            'linux': ''
        },

        'magickey_config/MagicKey_KV.yml': {
            'wes': '',
            'linux': ''
        },
        'magickey_config/MagicKeyConfig.yml': {
            'wes': '',
            'linux': ''
        },

        'passmark/autotest.ptscript': {
            'wes': '',
            'linux': ''
        },

        'target_pictures/linux/desktop.jpg': '330eba2e232fe6c2d8ee283aac92d675',
        'target_pictures/linux/hp_logo.jpg': '17688adf0ae415960ecb05eaa4a56d75',
        'target_pictures/linux/shutdown.jpg': '69875ce5a7c5cfe25e48bc62237aa218',
        'target_pictures/wes/desktop.jpg': '94f12b0591bd01a423bd1d13980a3586',
        'target_pictures/wes/hp_logo.jpg': 'b2a108b121855cf9b5f20697c6493e62',
        'target_pictures/wes/shutdown.jpg': '0b0b14d2d612986e135961c75477ed1d',

        'td_common/function_tool_version.yml': {
            'wes': '',
            'linux': ''
        },
        'td_common/global_config.yml': {
            'wes': '',
            'linux': ''
        },

        'td_thinupdate/ThinUpdate Capture and Deploy.xlsx': '0eb4ca285b69db290c54060671680a62',

        'xml/xml_map.yml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-AsuxAc87u.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-AsuxAc87u_5G.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-AsuxAx92u.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-AsuxAx92u_5G-1.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-AsuxAx92u_5G-2.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-NetgearAx80.xml': {
            'wes': '',
            'linux': ''
        },
        'xml/Wi-Fi-NetgearAx80-5G.xml': {
            'wes': '',
            'linux': ''
        },

        'elementLib.ini': {
            'wes': '',
            'linux': ''
        },
        'excle_template.xlsx': '',
        'hp.ico': 'b8d6677b757fba484ea2dfa5b0121793',
        'hp_icon.png': '2a51e973ddfb27ea2949320ef73b4019',
        'img.ico': '3e8ea37cc8b9eb34fe51faa45479340c',
        'main_bg.jpg': '8b8ca578d2bcc1e1c22185fdd31e3386',
        'man_config.yml': {
            'wes': '',
            'linux': ''
        },

        'script.yml': {
            'wes': '',
            'linux': ''
        },
        'scripts.xlsx': '4506cc6fa7a1e7166ba301ad468f0e56',
        'STM32_KV.yml': {
            'wes': '',
            'linux': ''
        },
    },

    'Test_Utility': {
        'Geekbench-5.2.0-Linux/GB.sh': '',
        'Geekbench-5.2.0-Linux/geekbench.plar': 'c99ba331e790c7a7525bf67e8122c204',
        'Geekbench-5.2.0-Linux/geekbench5': 'c51f17fe7ada43de41edddbc23190f1c',
        'Geekbench-5.2.0-Linux/geekbench_x86_64': '78ee0e9f77002a1cfffcef5768c5995d',
        'Geekbench-5.2.0-Linux/result': {
            'wes': '',
            'linux': ''
        },

        'BiosConfigUtility64.exe': '010f83f4188cc03d15fd2f1e8423f72a',
        'boot_agent.exe.lnk': '',
        'CrystalDiskMark5_1_2-en.exe': '5ceee11f8269ac6ba240493582e5b216',
        'CrystalDiskMark8_0_2.exe': '6e7f993f6cf98355bda032228f7a77c9',
        'cygwin1.dll': '1835f8f3aa1117c1a868bb6c8298399f',
        'DiskMark64.ini': {
            'wes': 'cc7c65958bfcec31f79e174ef011245b',
            'linux': ''
        },
        'iperf3.exe': '5be0a77f99022f42c1b946a17f092738',
        'iperf3_3.1.3-1_amd64.deb': '319170eddd26e42f71e292e119a7ed8a',
        'Key.txt': {
            'wes': '58a5cc1ef324201e5d3383e6c9c9637f',
            'linux': ''
        },
        'libiperf0_3.1.3-1_amd64.deb': '79d14003630156a240a20cdb83345662',
        'msdk.dll': '7d8db94157d44d992b1d2b9a2630ee08',
        'msedgedriver.exe': '8036bdadbab4ea0d3be2ec73caac231d',
        'petst.exe': '03f0a71e7f4d1731ea19b905690c80a6',
        'ROOTCA.cer': '23bb6780eba95856b09e71a6aba1d01d',
        'sp110277_LAN.exe': 'f015cc4664e8b61ef9f57bcee6fd96a1',
        'sp110955_Graphic.exe': '6881b22468c89e37a348c59447818a0d',
        'wol.exe': '7fa56c653a2bb236ba1fcfb30464c336'
    }
}


def check_integrity(depends: dict = REQUIRED_ITEMS) -> bool:
    status = False
    not_exist_list = []

    for root_path, sub_path in depends.items():
        for path, md5_value in sub_path.items():
            md5 = hashlib.md5()
            file_path = get_current_dir(root_path, path)

            if isinstance(md5_value, dict):
                md5_value = md5_value['wes'] if 'window' in platform.platform().lower() else md5_value['linux']

            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                md5.update(file_data)
                file_md5 = md5.hexdigest()

                if md5_value != '' and file_md5 != md5_value:
                    not_exist_list.append(file_path)
                    log.info(f"[common][check_integrity][{path}]this file md5 is: {file_md5}")
                    log.error(f"[common][check_integrity]the content of the file is incomplete: {file_path}")

            else:
                not_exist_list.append(file_path)
                log.error(f"[common][check_integrity]this file path cannot be accessed: {file_path}")

    if len(not_exist_list) == 0:
        status = True
    else:
        status = False
    return status


def recover_ini_env():
    if 'window' in platform.platform().lower():
        if os.path.exists(get_current_dir('Test_Report')):
            try:
                shutil.rmtree(get_current_dir('Test_Report'))
                log.info(f"[common][recover_ini_env]this dir is deleted: {get_current_dir('Test_Report')}")
            except Exception:
                log.error(f"[common][recover_ini_env]get exception when removing dirs: {traceback.format_exc()}")
        else:
            log.info(f"[common][recover_ini_env]this dir not exists: {get_current_dir('Test_Report')}")

        # admin_auto_start = r"C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\perf.link"
        # if os.path.exists(admin_auto_start):
        #     try:
        #         os.remove(admin_auto_start)
        #         log.info(f"[common][recover_ini_env]this file is deleted: {admin_auto_start}")
        #     except Exception:
        #         log.error(f"[common][recover_ini_env]get exception when removing file: {traceback.format_exc()}")
        # else:
        #     log.info(f"[common][recover_ini_env]this dir not exists: {admin_auto_start}")
        #
        # sys_auto_start = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\boot_agent.exe.lnk"
        # if os.path.exists(sys_auto_start):
        #     try:
        #         os.remove(sys_auto_start)
        #         log.info(f"[common][recover_ini_env]this file is deleted: {sys_auto_start}")
        #     except Exception:
        #         log.error(f"[common][recover_ini_env]get exception when removing file: {traceback.format_exc()}")
        # else:
        #     log.info(f"[common][recover_ini_env]this dir not exists: {sys_auto_start}")

    else:
        log.warning(f"[common][recover_ini_env]linux part of this method will be implemented")


def timer(name):
    def use_time(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            rs = func(*args, **kwargs)
            end_time = time.time()
            print('{} used time:{}'.format(name, end_time - start_time))
            return rs

        return wrapper

    return use_time


def get_ui_item(root_and_type, name: str, search_depth: int, search_wait: float = 0):
    item = root_and_type(searchDepth=search_depth, Name=name, searchWaitTime=search_wait)
    if not item.Exists():
        raise Exception(f"Cannot find UI item: \"{name}\"")
    return item


def is_admin():
    if OS == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except OSError:
            return False
    else:
        return True


def get_serial_port(name: str):
    coms = list(serial.tools.list_ports.comports())
    for com in coms:
        print(com.description)
        if name.lower() in com.description.lower():
            return com.description[-5:-1]


def __get_element_mapping():
    """
    # element format:
    # define name:"name":automationid:controltype
    # eg.: OKButton:"OK":Button----->By name
    #      CancelButton:btnCancel:Button----->By automationId
    :return: element
    """
    mappingDict = {}
    lines = TxtOperator(get_current_dir('Test_Data', 'elementLib.ini')).get_lines()
    for line in lines:
        if line[0] == '#':
            continue
        items = line.strip().split(":", 1)
        mappingDict[items[0]] = items[1]
    return mappingDict


def get_element(name, regex=True, **kwargs):
    # name is defined name, format: defined name:"Name"/AutomationId:ControlType
    elementId = __get_element_mapping()[name].split(':')[0].split(',')
    control_type = __get_element_mapping()[name].split(':')[1].upper()
    if elementId[0].startswith('"') and elementId[0].endswith('"'):
        if len(elementId) == 1:
            if regex:
                return getElementByType(control_type, RegexName=elementId[0].replace('"', ''), **kwargs)
            else:
                return getElementByType(control_type, Name=elementId[0].replace('"', ''), **kwargs)
        else:
            if regex:
                return getElementByType(control_type,
                                        RegexName=elementId[0].replace('"', ''),
                                        AutomationId=elementId[1],
                                        **kwargs)
            else:
                return getElementByType(control_type,
                                        Name=elementId[0].replace('"', ''),
                                        AutomationId=elementId[1]
                                                     ** kwargs)
    else:
        return getElementByType(control_type, AutomationId=elementId[0], **kwargs)


def wait_element(element, cycles=5, exists=True):
    """
    check element for specific times, default cycles 5
    :param element:
    :param cycles: specific check loops
    :param exists: sometimes you need check element not exist, set this value False
    :return:
    if exists set true, return element and None
    if exists set False, return True and None
    """
    flag = None
    if exists:
        for i in range(cycles):
            if element.Exists(0, 0):
                flag = element
                break
            else:
                flag = None
                time.sleep(1)
                continue
    else:
        for i in range(cycles):
            if element.Exists(0, 0):
                time.sleep(1)
                continue
            else:
                flag = True
                break
    return flag


def wait_next_element(current_ele, next_ele, action='click', cycle=5):
    if action.lower() == 'click':
        for i in range(cycle):
            if current_ele.Exists(1, 1):
                current_ele.Click()
            time.sleep(5)
            if next_ele.Exists(1, 1):
                return True
        return False


def wol_wakeup(mac, times=1, interval=0.5):
    wol_path = get_current_dir("Test_Utility/wol.exe")
    for i in range(times):
        log.info("WOL Command Send To {}".format(mac))
        os.system("{} {}".format(wol_path, mac))
        time.sleep(interval)
    return True


def disable_uac():
    os.popen(r'C:\Windows\System32\cmd.exe /k %windir%\System32\reg.exe ADD HKLM\SOFTWARE\Microsoft\Windows'
             r'\CurrentVersion\Policies\System /v EnableLUA /t REG_DWORD /d 0 /f')


def enable_uac():
    os.popen(r'C:\Windows\System32\cmd.exe /k %windir%\System32\reg.exe ADD HKLM\SOFTWARE\Microsoft\Windows'
             r'\CurrentVersion\Policies\System /v EnableLUA /t REG_DWORD /d 1 /f')


def start_jperf_server():
    pass


def get_win10_release_id():
    """
    Get the version number of win10
    :return: int
    """
    registry = registry_operator.RegistryTools()
    key = registry.open(path=r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    version = registry.get_value(key, 'ReleaseId')
    assert version, r'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ReleaseId not exists'
    return version[0]


def get_win10_mark():
    file = get_current_dir('Test_Data', 'excle', 'win10_mark.yml')
    print(file)
    obj = YamlOperator(file)
    content = obj.read()
    release_id = get_win10_release_id()
    log.info("{}".format(release_id))
    system_os = content.get(release_id)
    log.info("{}".format(system_os))
    assert system_os, 'lost key {} in {}'.format(release_id, file)
    return system_os


def get_wes_os_type():
    wmiobj = GetObject('winmgmts:/root/cimv2')
    operating_systems = wmiobj.ExecQuery("Select * from Win32_OperatingSystem")
    for o_s in operating_systems:
        os_name = o_s.Caption
        os_bit = o_s.OSArchitecture
        if 'Windows 10' in os_name:
            os_type = os_name
            break
        elif 'Windows Embedded Standard' in os_name and '64' in os_bit:
            os_type = 'WES7P'
            break
        elif 'Windows Embedded Standard' in os_name and '32' in os_bit:
            os_type = 'WES7E'
            break
    else:
        os_type = ''
    assert os_type, 'failed to get system actual os type'
    return os_type


def isExist_Process(processname):
    """find process isexist"""
    log.info("Process to be found：" + processname)
    pids = psutil.pids()
    for pid in pids:
        p = psutil.Process(pid)
        if p.name() == processname:
            log.info("Existing process:" + processname)
            return True
    else:
        log.info("not found")


def server_iperf3_control():
    tool_path_iperf = OSTool.get_current_dir("Test_Utility", 'iperf3.exe')
    os.system('{} -s'.format(tool_path_iperf))
    return True


def run_power_shell(command):
    codec = locale.getdefaultlocale()[1]
    log.info('the system codec is {}'.format(codec))
    args = [r"powershell", "-ExecutionPolicy", "Unrestricted"]
    if type(command) == list:
        command = args + command
    else:
        command = args + [command]
    out_byte = subprocess.run(command, stdout=subprocess.PIPE).stdout
    out_str = out_byte.decode(codec)
    return out_str


class NetWorkDisableEnable:
    """enable network"""

    def enable_internet(self):
        run_power_shell('netsh interface set interface Ethernet enabled')

        log.info(f"[common][enable_internet]run cmd:netsh interface set interface Ethernet enabled")

        return True

    "disable network"

    def disable_internet(self):
        run_power_shell('netsh interface set interface Ethernet disabled')

        log.info(f"[common][disable_internet]run cmd:netsh interface set interface Ethernet disabled")

        return True

    def enable_wlan(self):
        run_power_shell("netsh interface set interface name='Wi-Fi' admin ='enabled'")

        log.info(f"[common][enable_wlan]run cmd:netsh interface set interface name='Wi-Fi' admin ='enabled'")

        return True

    def disable_wlan(self):
        run_power_shell("netsh interface set interface name='Wi-Fi' admin ='disabled'")

        log.info(f"[common][disable_wlan]run cmd:netsh interface set interface name='Wi-Fi' admin ='disabled'")


class NetWorkDisableEnablelinux:
    def disable_lan(self):
        subprocess.Popen("/usr/lib/hptc-network-mgr/common/netmgr_wired --down eth0 && ifconfig eth0 down")


def get_global_gateway():
    global_config = OSTool.get_current_dir('Test_Data', 'td_common', 'global_config.yml')
    global_config_yml = YamlOperator(global_config)
    global_config_data = global_config_yml.read()
    network = global_config_data.get('network')
    gateway = network.get('gateway')
    return gateway


def get_server_ip():
    if not os.path.exists('server.txt'):
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
    else:
        with open("server.txt", "r") as f:
            server_ip = f.read()
    return server_ip


def get_diskmark_version():
    yml_path = OSTool.get_current_dir('Test_Data', 'td_common', 'function_tool_version.yml')
    data = YamlOperator(yml_path).read()
    dismark = data.get('diskmark')
    version = dismark.get('version')
    return version


def alter(file, old_str, new_str):
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with open(file, "w", encoding="utf-8") as f:
        f.write(file_data)
    return True


def get_lan_version():
    yml_path = OSTool.get_current_dir('Test_Data', 'td_common', 'function_tool_version.yml')
    data = YamlOperator(yml_path).read()
    lan = data.get('lan')
    if OS == 'Linux':
        lib_version = lan.get('linux_lib_iperf')
        jper_version = lan.get('linux_iperf')
        return lib_version, jper_version
    else:
        imperf3_version = lan.get('win_iperf')
        return imperf3_version


def run_powershell_byte(command):
    codec = locale.getdefaultlocale()[1]
    log.info('the system codec is {}'.format(codec))
    args = [r"powershell", "-ExecutionPolicy", "Unrestricted"]
    if type(command) == list:
        command = args + command
    else:
        command = args + [command]
    out_byte = subprocess.run(command, stdout=subprocess.PIPE).stdout
    return out_byte


def get_cpu_core():
    """
    get cpu core and speed
    :return: str
    """
    processor_info = subprocess.getoutput('dmidecode -t processor')
    cpu_core_value = re.findall(r'(?i)Core Count:\s+(.*?)\n', processor_info, re.S)[0]
    log.info('cpu_core value:{}'.format(cpu_core_value))
    if cpu_core_value:
        cpu_core = cpu_core_value
    else:
        cpu_core = ''
    return cpu_core


def get_ml():
    mlpath = r"SYSTEM\CurrentControlSet\Control\WindowsEmbedded\RunTimeID"
    reg = RegistryTools()
    ml = reg.get_value(reg.open(mlpath), 'RunTimeOEMRev')[0][:11]
    return ml


def is64windows():
    return 'PROGRAMFILES(X86)' in os.environ


def get_serial_port(name: str):
    coms = list(serial.tools.list_ports.comports())
    for com in coms:
        print(com.description)
        if name.lower() in com.description.lower():
            return com.description[-5:-1]


def wakeup_uut(mac):
    wol = get_current_dir('Test_Utility', 'WOL.exe')
    cmd = '{} {}'.format(wol, mac)
    run_power_shell(cmd)


def get_element_plus(element_name, count=6):
    for i in range(count):
        element = get_element(element_name)
        if element.Exists():
            return element
    else:
        return False


class SendKey(threading.Thread):
    def __init__(self, physical_key, kn, t=0.3):
        threading.Thread.__init__(self)
        self.hand = physical_key
        self.kn = kn
        self.t_flag = True
        self.t = t

    def run(self):
        log.info('Start Cycle Press The Key : ' + str(self.kn) + ' ...')
        while self.t_flag:
            self.hand.key(self.kn, t=self.t)
            print('Sending {}'.format(self.kn))

    def stop(self):
        self.t_flag = False
        log.info('Stop Cycle Press The Key : ' + str(self.kn) + ' ...')


class HpThinUpdatePanel:
    system_path = r"C:\Program Files\HP\HP ThinUpdate\ThinUpdate.exe"
    if 'window' in platform.platform().lower():
        __instance = get_element('THIN_MAIN_WINDOW')

    def __init__(self):
        self.config = YamlOperator(get_current_dir('Test_Data/td_thinupdate/global_config.yml')).read()
        self.local_folder_path = ''

    @classmethod
    def __refresh_instance(cls):
        cls.__instance = get_element('THIN_MAIN_WINDOW')
        return cls.__instance

    def get_instance(self):
        return self.__instance

    @classmethod
    def open_panel(cls):
        log.info('[common-hpthinupdate]begin to launch Thinupdate')
        subprocess.Popen(cls.system_path)
        if not cls.__instance.Exists():
            os.popen(cls.system_path)
            time.sleep(5)
        for i in range(60):
            if cls.__refresh_instance().Exists():
                log.info('[common-hpthinupdate]Thin update successfully launched')
                return True
            else:
                log.info('[common-hpthinupdate]Instance not Found')
                time.sleep(2)
        return False

    @classmethod
    def close_panel(cls):
        if cls.__refresh_instance().Exists():
            for i in range(5):
                if get_element('ERROR_DIALOG').Exists():
                    get_element('ERROR_DIALOG').Close()
                    time.sleep(1)
                else:
                    break
            cls.__instance.Close()
            time.sleep(2)

    def validate_server(self):
        """
        check if Thin update connected to ftp server
        :return:
        """
        for i in range(60):
            # wait 60s for connecting to ftp server
            plat_comb = get_element('PLATFORM_COMB')
            plat_comb.Expand()
            plat_comb.Click(0, 0)
            if len(plat_comb.GetChildren()):
                log.info('[dl_img] Successfully connect to ftp server')
                return True
            else:
                log.info('checking ftp server connected...{}'.format(i))
                if get_element('ERROR_DIALOG').Exists():
                    log.error('There is Error when connecting to ftp server')
                    for _ in range(3):
                        # if connect to server fail, there will be some error dialogs
                        if get_element('ERROR_DIALOG').Exists():
                            get_element('ERROR_DIALOG').Close()
                            time.sleep(1)
                        else:
                            self.close_panel()
                            return False
                else:
                    time.sleep(1)
                    continue
        self.close_panel()
        return False

    def close_thinupdate_window(self):
        thinupdate_window: ui.WindowControl = get_element_plus('THINUPDATE_WINDOW')
        if not thinupdate_window:
            log.info('Fail to find ThinUpdate window.')
            return False
        else:
            thinupdate_window.Close()
            self.__instance = None
            return True

    @staticmethod
    def kill_thinupdate_process():
        subprocess.Popen('taskkill /F /IM ThinUpdate.exe')

    @staticmethod
    def __parse_addr(folder_path):
        msi_file_path = ''
        win64 = is64windows()
        if win64:
            msi_name = 'SetupHPThinUpdateWin64.msi'
        else:
            msi_name = 'SetupHPThinUpdate.msi'
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file in files:
                file_path = os.path.join(root, file).replace('/', '\\')
                if msi_name in file_path:
                    msi_file_path = file_path
        return msi_file_path

    @staticmethod
    def redirect_ftp_server(ip):
        reg = registry_operator.RegistryTools()
        try:
            # "\HKEY_LOCAL_MACHINE\SOFTWARE\HP\ThinUpdate"
            key = reg.open(r'SOFTWARE\HP\ThinUpdate')
            reg.create_value(key, 'ftp_server', content=ip)
        except Exception as e:
            log.error(e)

    def download_install_package_folder(self, version):
        server = self.config.get('thinupdate_ftp_server')
        username = self.config.get('ftp_user')
        passwd = self.config.get('ftp_pwd')
        try:
            ftp = file_transfer.FTPUtils(server, username, passwd)
            remote_folder_path = '/Function/Projects/Ad-hoc Testing/HP ThinUpdate/{}'.format(version)
            local_folder_path = 'c:/{}'.format(version)
            # local_folder_path = os.path.join(get_current_dir(), 'Test_Data/{}'.format(version))
            if not os.path.exists(local_folder_path):
                os.makedirs(local_folder_path)
            ftp.download_dir(remote_folder_path, local_folder_path)
            log.info('Downloading installation packages...')
            time.sleep(10)
            ftp.close()
        except:
            log.error('Error occurred when download package from ftp:\n{}'.format(traceback.format_exc()))
            return False
        if os.path.exists(local_folder_path):
            self.local_folder_path = local_folder_path
            return True
        else:
            return False

    @staticmethod
    def query_thinupdate():
        """
        Query ThinUpdate with wmi. If installed, set flag[0] to True and get version number.
        :return: [Bool, version]
        """
        flag = [False, '']
        wmi = GetObject(r'winmgmts:\\.\root\cimv2')
        wql = "Select * from Win32_Product"
        rs = wmi.ExecQuery(wql)
        for r in rs:
            if r.name:
                if r.name.upper() == 'HP THINUPDATE':
                    flag[0] = True
                    flag[1] = r.version
                    break
            else:
                continue
        return flag


class BCUConfig:
    def __init__(self, file):
        """
        Config data expect orderly
        :param file:
        """
        self.file = file
        self.config = self.__analyze_config()

    def __analyze_config(self):
        """
        read bcu config data, and convert to dict
        :return:
        """
        result = {}
        with open(self.file) as f:
            data = f.readlines()
        temp_key = ''
        for line in data:
            if line[0] == '	' or line[0] == ';':
                result[temp_key].append(line.strip())
            else:
                temp_key = line.strip()
                result[temp_key] = []
        return result

    def __save_data(self):
        result = ''
        for k, v in self.config.items():
            result = result + k + '\n'
            for i in v:
                if i and ';' == i[0]:
                    result = result + i + '\n'
                else:
                    result = result + '\t' + i + '\n'
        with open(self.file, 'w') as f:
            f.write(result)

    def enable_values(self, key, values, match=False):
        """
        :param key: strictly match item key in files
        :param values: list: select enabled list of values
        :param match: support key word if match is false, else strictly match value name except capital and small letter
        :return: success return True | not match return False
        """
        for value in values:
            flag = self.enable(key, value, match)
            if flag:
                return True
        return False

    def enable(self, key, value, match=False):
        """
        :param key: strictly match item key in files
        :param value: select enabled value
        :param match: support key word if match is false, else strictly match value name except capital and small letter
        :return: success return True | not match return False
        """
        data = self.config[key]
        result = []
        get_key_flag = False
        for item in data:
            if match:
                if value.upper() == item.upper():
                    result.append('*' + item)
                    get_key_flag = True
                elif value.upper() == item.replace('*', '').upper():
                    return True
                elif item.startswith('*'):
                    result.append(item[1:])
                else:
                    result.append(item)
            else:
                if value.upper() in item.upper():
                    if item.startswith('*'):
                        return True
                    result.append('*' + item)
                    get_key_flag = True
                elif item[0] == '*':
                    result.append(item[1:])
                else:
                    result.append(item)
        if not get_key_flag:
            return False
        self.config[key] = result
        self.__save_data()
        return True

    def reorder(self, key, value, index):
        data = self.config[key]
        for item in data:
            if value.upper() in item.upper():
                data.remove(item)
                data.insert(index - 1, item)
                break
        self.config[key] = data
        self.__save_data()

    def set_value(self, key_word, value, include=None, add=None):
        key = ''
        for k, v in self.config.items():
            if key_word in k:
                key = k
        data = self.config[key]
        if include:
            for d in data:
                if include in d:
                    index = data.index(d)
                    if not add:
                        data[index] = value
                    else:
                        data[index] += value
        else:
            data[0] = value
        self.config[key] = data
        self.__save_data()

    def transform(self, key):
        new_key = ''
        for k, v in self.config.items():
            if key in k:
                new_key = k
        return new_key


class WriteFilter:
    if os.path.exists(r'C:\Program Files\HP\HP Write Manager\HPWFConfig.exe'):
        path = r'C:\Program Files\HP\HP Write Manager\HPWFConfig.exe'
    elif os.path.exists(r'C:\Program Files (x86)\HP\HP Write Manager\HPWFConfig.exe'):
        path = r'C:\Program Files (x86)\HP\HP Write Manager\HPWFConfig.exe'
    else:
        path = ''

    def __init__(self):
        self.hpwm_wnd = get_element('HPWM_WINDOW')
        pass

    def open_panel(self):
        if self.path != '':
            os.popen(self.path)
            self.hpwm_wnd = wait_element(self.hpwm_wnd, 60, True)
            return True
        else:
            return False

    def close_panel(self):
        for i in range(30):
            if self.hpwm_wnd.Exists():
                self.hpwm_wnd.Close()
                return True
            else:
                time.sleep(1)
                continue

    def check_state_ui(self):
        if not self.hpwm_wnd.Exists():
            self.open_panel()
            time.sleep(3)
        if self.hpwm_wnd.get_element('HPWM_DISABLE').CurrentIsSelected():
            return 'DISABLED'
        elif self.hpwm_wnd.get_element('HPWM_HPWF').CurrentIsSelected():
            return 'HPWF'
        elif self.hpwm_wnd.get_element('HPWM_UWF').CurrentIsSelected():
            return 'UWF'
        elif self.hpwm_wnd.get_element('HPWM_FBWF').CurrentIsSelected():
            return 'FBWF'
        elif self.hpwm_wnd.get_element('HPWM_EWF').CurrentIsSelected():
            return "EWF"
        else:
            return "UNKNOWN"

    def check_state(self):
        if os.path.exists(r'c:\windows\sysnative\uwfmgr.exe'):
            if ui.ButtonControl(RegexName='Current session: HPWF.*').Exists():
                return 'HPWF'
            elif ui.ButtonControl(RegexName='Current session: UWF.*').Exists():
                return 'UWF'
            else:
                return 'DISABLED'

    @staticmethod
    def add_exclusion(path: str):
        device_letter, file_path = path.split(':')
        cmd = os.popen(r'c:\windows\sysnative\hpwritefctrl.exe -addexclusion {}: {}'.format(device_letter, file_path))
        if 'adding exclusion' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def enable_hpwf_cmd():
        cmd = os.popen(r'c:\windows\sysnative\hpwritefctrl.exe -enable')
        if 'filer will be enabled on next boot' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def enable_uwf_cmd():
        cmd = os.popen(r'c:\windows\sysnative\uwfmgr.exe filter enable')
        if 'unified write filter will be enabled after system restart' in cmd.read().lower() or \
                'unified write filter already enabled' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def enable_fbwf():
        cmd = os.popen(r'c:\windows\sysnative\fbwfmgr.exe /enable')
        if 'file-based write filter will be enabled on next reboot' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def enable_ewf():
        os.popen(r'c:\windows\sysnative\ewfmgr.exe c: -enable')
        return True

    def disable_hpwm(self):
        if not self.hpwm_wnd.Exists():
            self.open_panel()
            time.sleep(3)
        self.hpwm_wnd.get_element('HPWM_DISABLE').GetChildren()[0].Click()
        self.hpwm_wnd.get_element('OK').Click()
        for i in range(30):
            if self.hpwm_wnd.get_element('HPWM_WINDOW').Exists():
                self.hpwm_wnd.get_element('CANCEL').Click()
                break
            else:
                time.sleep(1)
                continue

    @staticmethod
    def disable_hpwf_cmd():
        cmd = os.popen(r'c:\windows\sysnative\hpwritefctrl.exe -disable')
        if 'filer will be disabled on next boot' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def disable_uwf_cmd():
        cmd = os.popen(r'c:\windows\sysnative\uwfmgr.exe filter disable')
        if 'unified write filter will be disabled after system restart' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def disable_fbwf_cmd():
        cmd = os.popen(r'c:\windows\sysnative\fbwfmgr.exe /disable')
        if 'file-based write filter will be disabled on the next reboot' in cmd.read().lower():
            return True
        else:
            return False

    @staticmethod
    def disable_ewf_cmd():
        os.popen(r'c:\windows\sysnative\ewfmgr.exe c: -disable')
        return True

    @staticmethod
    def get_file_exclusions_cmd(name):
        os.popen(r'c:\windows\sysnative\hpwritefctrl.exe -getexclusions c: >>c:\temp\{}'.format(name))
        return True

    @staticmethod
    def get_markers_cmd(name):
        os.popen(r'c:\windows\sysnative\hpwritefctrl.exe -getmarkers c: >c:\temp\{}'.format(name))
        return True

    @staticmethod
    def get_register_cmd(name):
        os.popen(r'c:\windows\sysnative\hpregfctrl.exe -getexclusions c: >>c:\temp\{}'.format(name))
        return True


def logo_on_admin(username="Admin", password="Admin", domain=""):
    """
    Before program, Please Add HKLM\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon
    To Registry exclusions of Write Filter
    """
    root = win32con.HKEY_LOCAL_MACHINE
    key = win32api.RegOpenKeyEx(root, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon', 0,
                                win32con.KEY_ALL_ACCESS | win32con.KEY_WOW64_64KEY | win32con.KEY_WRITE)
    win32api.RegSetValueEx(key, "AutoAdminLogon", 0, win32con.REG_SZ, '1')  # auto logon
    win32api.RegSetValueEx(key, "DefaultUserName", 0, win32con.REG_SZ, username)
    win32api.RegSetValueEx(key, "DefaultPassWord", 0, win32con.REG_SZ, password)
    if domain != "":
        win32api.RegSetValueEx(key, "DefaultDomain", 0, win32con.REG_SZ, domain)


def read_function_tool_yaml():
    yaml_path = OSTool.get_current_dir('Test_Data', 'td_common', 'function_tool_version.yml')
    value = YamlOperator(yaml_path)
    return value.read()


def is_controller():
    # windows/wes, this will represent controller or thin client
    if os.path.exists(r'c:\windows\sysnative\hpramdiskcpl.exe') or 'linux' in platform.platform().lower():
        return False
    else:
        return True


def edit_Screen_baterry_wes():
    log.info('this system is ')
    display = 'powercfg /CHANGE /monitor-timeout-ac 0'
    sleep = 'powercfg /CHANGE /standby-timeout-ac 0'
    run_power_shell(display)
    time.sleep(2)
    run_power_shell(sleep)
    run_power_shell('netsh firewall set opmode disable')
    return True


def edit_Screen_baterry():
    subprocess.getoutput('mclient --quiet set root/Power/default/AC/standby 0 && mclient commit '
                         '&& mclient --quiet set root/Power/default/AC/sleep 0 && mclient commit'
                         '&& mclient --quiet set root/Power/default/battery/low/sleep 0 && mclient commit '
                         '&& mclient --quiet set root/Power/default/battery/low/standby 0 && mclient commit '
                         '&& mclient --quiet set root/screensaver/timeoutScreensaver 0 && mclient commit ')

    standby_value = subprocess.Popen("mclient --quiet get root/Power/default/AC/standby && "
                                     "mclient --quiet get root/Power/default/AC/sleep && "
                                     "mclient --quiet get root/Power/default/battery/low/sleep &&"
                                     "mclient --quiet get root/Power/default/battery/low/standby &&"
                                     "mclient --quiet get root/screensaver/timeoutScreensaver", shell=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    value = standby_value.stdout.read().decode()
    value_list = value.strip().split('\n')
    log.info('[edit_Screen_linux] value list value:{}'.format(value_list))
    number = value_list.count('0')
    log.info('[edit_Screen_linux] value list appear 0 num:{}'.format(number))
    if number == 5:
        os.system('systemctl disable firewalld')
        return True
    else:
        return False


def get_txt_content(filename=''):
    with open('{}'.format(filename), 'r') as f:
        value = f.read()
    return value


def read_uut_info():
    if os.path.exists('uut_info.txt'):
        f = open('uut_info.txt')
        value_list = f.readlines()
        return value_list


if is_controller():
    import pytesseract
"""
need install tesseract-ocr-w64-v5.0.0.exe
path:\\15.83.240.98\Automation\tools\tesseract-ocr-w64-v5.0.0.exe
"""

if is_controller():
    file_ver4 = r'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
    file_ver5 = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
    for file in [file_ver4, file_ver5]:
        if os.path.exists(file):
            pytesseract.pytesseract.tesseract_cmd = r'C://Program Files/Tesseract-OCR/tesseract.exe'
            break
    else:
        raise FileNotFoundError


def recognize_string(pic_path, platform_name, lang='automation3'):
    """
    Recognize characters in picture according to different lang parameters.
    :param pic_path: Full path of picture.
    :param lang: candidate value: 'automation3', 'eng', ''
    :return: A list of recognized characters.
    """
    log.info('Start recognizing string in picture')
    t_list = []
    pic = pic_path
    if lang:
        try:
            image = Image.open(pic)
            if 'm' in platform_name.lower():
                gray = image.convert('L')
                invert_pic = ImageOps.invert(gray)
            else:

                invert_pic = ImageOps.invert(image)
            pytesseract.pytesseract.tesseract_cmd = r'C://Program Files/Tesseract-OCR/tesseract.exe'
            text = pytesseract.image_to_string(invert_pic, lang='eng')  # lang=automation3, lang=eng
            log.info('[recognize_string]text: \n{}\n'.format(text))
            t_list = text.split('\n')
            t_list = [i for i in t_list if i != '']
        except Exception as e:
            log.info('[recognizer][recognize_string]error occurs when recognize string from picture.\n{}'.format(e))
        finally:
            return t_list
    else:
        try:
            res = ocr_client.get_results(image_path=pic_path)
            log.info('ocr_client get result: {}'.format(res))
            for k, v in res.items():
                if k == 'labels':
                    t_list = v
                    break
        except Exception as e:
            log.info('[recognizer][recognize_string]error occurs when use ocr client to recognize string from '
                     'picture.\n{}'.format(e))
        finally:
            return t_list


def system_change(params):
    if isinstance(params, int) and 32 > params:
        bin_data = '1' * params + '0' * (32 - params)
        start = 0
        end = 8
        bin_list = []
        while len(bin_data) >= end:
            a = bin_data[start:end]
            start += 8
            end += 8
            b = int(a, 2)
            bin_list.append(str(b))
        return '.'.join(bin_list)


def change_bin_ip(bin_info):
    start = 0
    bin_list = []
    while len(bin_info) >= start + 8:
        end = start + 8
        a = bin_info[start:end]
        start += 8
        b = int(a, 2)
        bin_list.append(str(b))
    return bin_list


def change_ip_bin(ip):
    ip_list = ip.split('.')
    bin_ip_list = []
    for i in ip_list:
        bin_ip_list.append(bin(int(i)).replace('0b', '').rjust(8, '0'))
    return bin_ip_list


def rang_of_ip(ip, submask):
    ip_bin_list = change_ip_bin(ip)
    submask_bin_list = change_ip_bin(submask)
    one_index = ''.join(submask_bin_list).find('0')
    submask_bin = ''.join(submask_bin_list)[0:one_index]
    ip_bin = ''.join(ip_bin_list)[0:one_index]
    net_int_addr = int(submask_bin, 2) & int(ip_bin, 2)
    with_bin_net = bin(net_int_addr).replace('0b', '').rjust(one_index, '0')
    net_bin_addr = change_bin_ip(with_bin_net.ljust(32, '0'))
    broad_bin_addr = change_bin_ip(with_bin_net.ljust(32, '1'))

    return net_bin_addr, broad_bin_addr


def get_range_iplist(ip, mask):
    mask = ipaddress.ip_address(mask)
    mask = int(bin(mask._ip).count('1'))

    if mask > 0 and mask <= 30:
        submask = system_change(mask)
        network, broadcast = rang_of_ip(ip, submask)
        params_network = copy.deepcopy(network)
        params_broadcast = copy.deepcopy(broadcast)
        params_network[-1] = str(int(params_network[-1]) + 1)
        params_broadcast[-1] = str(int(params_broadcast[-1]) - 1)
        start_ip = params_network
        end_ip = params_broadcast
        ip_count = 2 ** (32 - mask) - 2

        network = '{}.{}.{}.{}'.format(*network)
        broadcast = '{}.{}.{}.{}'.format(*broadcast)
        data = {
            'ip_count': ip_count,
            'submask': submask,
            'network': network,
            'broadcast': broadcast,
            'start_ip': start_ip,
            'end_ip': end_ip
        }
        return {'msg': '', 'data': data, 'code': '00000'}
    else:
        return {'msg': 'ERROR', 'data': '', 'code': '00000'}


def update_broadcast():
    broadcast = get_range_iplist(ip='', mask='')
