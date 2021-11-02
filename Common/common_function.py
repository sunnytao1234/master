import copy
import ctypes
import locale
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time

import pyautogui
import pykeyboard
import pymouse
import yaml

from Common.file_operator import YamlOperator
from Common.log import log, get_current_dir

if 'windows' in platform.platform().lower():
    OS = 'Windows'
    import pythoncom

    pythoncom.CoInitialize()
    import win32api, win32con
    from win32com.client import GetObject
    import wmi
else:
    OS = 'Linux'

mouse = pymouse.PyMouse()
kb = pykeyboard.PyKeyboard()


def check_ip_yaml():
    ip_yaml_path = get_current_dir('Test_Data', 'ip.yml')
    if os.path.exists(ip_yaml_path):
        with open(ip_yaml_path, encoding='utf-8') as f:
            ip = yaml.safe_load(f)
            if ip:
                return ip[0]
            else:
                return '127.0.0.1'
    else:
        f = open(ip_yaml_path, 'w')
        f.close()
        with open(ip_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump([OSTool.get_ip()], f, default_flow_style=False)
        return OSTool.get_ip()


class OSTool:
    @classmethod
    def reboot(cls):
        if 'window' in OS:
            os.system('shutdown -r -t 3')
        else:
            os.system('reboot')

    @classmethod
    def run_as_admin(cls, func):
        def wrapper(*args, **kwargs):
            if cls.is_admin():
                log.info('current is admin mode')
                func(*args, **kwargs)
            else:
                if 'window' in OS.lower():
                    log.info('current is not admin mode, try to run as admin')
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                else:
                    log.info('current is user mode for linux agent')
                    func(*args, **kwargs)

        return wrapper

    @classmethod
    def is_admin(cls):
        if 'window' in OS.lower():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except OSError:
                return False
        else:
            if os.path.exists('/var/run/hptc-admin'):
                return True
            else:
                return False

    @classmethod
    def __judge_has_root_pw_linux(cls):
        s = subprocess.call("hptc-passwd-default --root --check >/dev/null 2>&1", shell=True)
        if s:
            return True
        else:
            return False

    @classmethod
    def switch_to_user_linux(cls):
        for _ in range(3):
            if not cls.is_admin():
                log.info("[common-func][ostool]switch to user mode success")
                return True
            else:
                os.system('hptc-switch-admin')
                time.sleep(1)
        if cls.is_admin():
            log.error("[common-func][ostool]switch to user mode fail after 3 tries")
            return False

    @classmethod
    def switch_to_admin_linux(cls):
        if cls.__judge_has_root_pw_linux():
            for _ in range(3):
                # try 3 times if modify fail, workaround
                if cls.is_admin():
                    log.info("[common-func][ostool]switch to Admin mode success")
                    return True
                else:
                    os.system('hptc-switch-admin')
                    kb.type_string('1')
                    time.sleep(1)
                    kb.press_key(kb.enter_key)
                    time.sleep(1)
                    if cls.is_admin():
                        log.info('[common-func][ostool]switch to root successfully')
                        return True
                    else:
                        # try with os in domain, need input user and password
                        kb.tap_key(kb.enter_key)
                        time.sleep(1)
                        kb.type_string('root')
                        time.sleep(1)
                        kb.tap_key(kb.tab_key)
                        time.sleep(1)
                        kb.type_string('1')
                        time.sleep(1)
                        kb.tap_key(kb.enter_key)
                        time.sleep(1)
        else:
            for _ in range(3):
                if cls.is_admin():
                    return True
                os.popen('hptc-switch-admin')
                time.sleep(2)
                kb.type_string('1')
                time.sleep(1)
                kb.tap_key(kb.tab_key)
                time.sleep(1)
                kb.type_string('1')
                time.sleep(1)
                kb.tap_key(kb.enter_key)
                time.sleep(2)
        if not cls.is_admin():
            log.error("[common-func][ostool]switch to admin mode fail after 3 tries")
            return False

    @classmethod
    def switch_user_win(cls, username="Admin", password="Admin", domain=""):
        """
        Before program, Please Add HKLM\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon
        To Registry exclusions of Write Filter
        """
        root = win32con.HKEY_LOCAL_MACHINE
        key = win32api.RegOpenKeyEx(root, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon', 0,
                                    win32con.KEY_ALL_ACCESS | win32con.KEY_WOW64_64KEY | win32con.KEY_WRITE)
        win32api.RegSetValueEx(key, "DefaultUserName", 0, win32con.REG_SZ, username)
        win32api.RegSetValueEx(key, "DefaultPassWord", 0, win32con.REG_SZ, password)
        if domain != "":
            win32api.RegSetValueEx(key, "DefaultDomain", 0, win32con.REG_SZ, domain)

    @classmethod
    def get_os_bit(cls):
        wmiobj = GetObject('winmgmts:/root/cimv2')
        operating_systems = wmiobj.ExecQuery("Select * from Win32_OperatingSystem")
        for o_s in operating_systems:
            os_bit = o_s.OSArchitecture
            if '64' in os_bit:
                os_type = 'x64'
            elif '32' in os_bit:
                os_type = 'x86'
            else:
                os_type = 'incorrect_os_type'
            return os_type

    @classmethod
    def get_ip(cls):
        if OS == 'Linux':
            wired_status = subprocess.getoutput("mclient --quiet get tmp/NetMgr/eth0/IPv4/status")
            if wired_status == "1":
                sys_eth0_ip = subprocess.getoutput("ifconfig | grep eth0 -A 1 | grep -i 'inet'")
                eth0_ip = re.search(r'(?i)(?:inet|inet addr)[: ]([\\.\d]+)', sys_eth0_ip)
                assert eth0_ip, 'Do not get ip'
                return eth0_ip.group(1) if eth0_ip else 0
            wireless_status = subprocess.getoutput("mclient --quiet get tmp/NetMgr/wlan0/IPv4/status")
            if wireless_status == "1":
                sys_wlan0_ip = subprocess.getoutput("ifconfig | grep wlan0 -A 1 | grep -i 'inet'")
                wlan0_ip = sys_wlan0_ip.strip().split()[1].split(":")[1]
                return wlan0_ip
            else:
                with os.popen("ifconfig | grep eth0 -A 1 | grep -i 'inet'") as f:
                    string = f.read()
                    eth0_ip = re.findall(r"eth0.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?lo", string, re.S)
                    if eth0_ip:
                        eth0_ip = eth0_ip[0]
                    else:
                        return
                return eth0_ip
        else:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip

    @classmethod
    def get_platform(cls):
        # platform for TC, eg. T630 mt42
        if OS == 'Linux':
            plat_form = subprocess.getoutput('/usr/bin/hptc-hwsw-id --hw')
            if plat_form == '':
                log.info('plat_form is empty.')
            return plat_form
        else:
            wmi_obj = GetObject(r'winmgmts:\\.\root\cimv2')
            wucol = wmi_obj.ExecQuery("Select Model from Win32_ComputerSystem")
            plat_form = 'Error'
            for s in wucol:
                plat_form = s.Model.lower()
                break
            return plat_form

    @classmethod
    def get_current_dir(cls, *args):
        """
        :param args: use like os.path.join(path, *path)
        :return: absolute path
        For Linux OS
        """
        current_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        if args:
            path = os.path.join(current_path, *args)
        else:
            path = current_path
        return "/".join(path.split("\\"))

    @classmethod
    def get_folder_items(cls, path, **kwargs):
        """
        get folder items without recursion
        :param path: str, support abs path and relative path
        :return:
        safe_mode: if folder not exist, create
        filter_name: get file by filter name
        file_only: ignore folder
        """
        safe_mode = kwargs.get("safe_mode", True)
        filter_name = kwargs.get("filter_name", "")
        file_only = kwargs.get("file_only", False)
        file_path = "/".join(os.path.realpath(path).split("\\"))
        if not os.path.exists(file_path) and safe_mode:
            os.makedirs(file_path)
        file_list = os.listdir(file_path)
        if filter_name:
            filter_name_list = []
            for i in file_list:
                if filter_name.upper() in i.upper():
                    filter_name_list.append(i)
            file_list = filter_name_list
        if file_only:
            for i in copy.deepcopy(file_list):
                dir_path = file_path + "/{}".format(i)
                if os.path.isdir(dir_path):
                    file_list.remove(i)
        return file_list

    @classmethod
    def get_folder_items_recursion(cls, path, **kwargs):
        """
        get all items of current folder and sub folders, except folder start with __ or .
        :param path:
        :param kwargs:
        :return:
        """
        file_list = cls.get_folder_items(path, **kwargs)
        all_file = []
        for i in file_list:
            new_path = os.path.join(path, i)
            if i[:2] == "__" or i[0] == '.':
                continue
            elif os.path.isdir(new_path):
                all_file = all_file + cls.get_folder_items_recursion(new_path, **kwargs)
            else:
                all_file.append(i)
        return all_file

    @classmethod
    def get_resolution(cls):
        return pyautogui.size()

    @classmethod
    def power_shell(cls, command):
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


class AddStartup:
    def __init__(self, name):
        r"""
        Windows:
        add shortcut for one file to startup folder:
        C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
        Linux:
        add one file to startup service
        :param name: file name with full path, c:/test/test.exe  or /root/temp/test
        """
        self.__name = name

    def add_startup(self):
        if OS == 'Windows':
            self.__add_wes_script_startup()
        else:
            # default as linux
            self.__add_linux_script_startup()

    @staticmethod
    def __create_shortcuts(target_path, name):
        # create shortcut using vbs
        os.system('echo ThePath = "{}">aaa.vbs'.format(target_path))
        os.system('echo lnkname = "{}.lnk">>aaa.vbs'.format(name))
        os.system('echo WS = "Wscript.Shell">>aaa.vbs')
        os.system('echo Set Shell = CreateObject(WS)>>aaa.vbs')
        os.system('echo Set Link = Shell.CreateShortcut(lnkname)>>aaa.vbs')
        os.system('echo Link.TargetPath = ThePath>>aaa.vbs')
        os.system('echo Link.Save>>aaa.vbs')
        os.system('echo Set fso = CreateObject("Scripting.FileSystemObject")>>aaa.vbs')
        os.system('echo f = fso.DeleteFile(WScript.ScriptName)>>aaa.vbs')
        os.system('start aaa.vbs')

    def __add_linux_script_startup(self):
        log.info('[common function][add startup]begin to add linux script as service')
        src = '/root/auto_start_setup.sh'
        src_auto = get_current_dir("auto.service")
        with open(src_auto, 'w') as f:
            datas = '[Unit]\nDescription=auto\n\n[Service]\n' \
                    'ExecStart=/root/auto_start_setup.sh\nAfter=hptc-network-mgr.service\n\n' \
                    '[Install]\nWantedBy=multi-user.target'
            f.write(datas)
        dst_auto = "/etc/systemd/system/auto.service"
        dst_wants = "/etc/systemd/system/multi-user.target.wants/auto.service"
        if os.path.exists(src):
            os.remove(src)
        os.system("fsunlock")
        time.sleep(0.2)
        with open('/etc/init/auto-run-automation-script.conf', 'w+') as f:
            f.write("start on lazy-start-40\nscript\n")
            f.write("\t/writable/root/auto_start_setup.sh\nend script\n")
        time.sleep(0.5)
        os.system("chmod 777 /etc/init/auto-run-automation-script.conf")
        os.system('fsunlock')
        time.sleep(0.1)
        bash_script = "#! /bin/bash\nsource /etc/environment\nsource /etc/profile\n" \
                      "sleep 20\nexport DISPLAY=:0\nfsunlock\ncd {path}\n".format(path=get_current_dir())
        with open('/writable/root/auto_start_setup.sh', 'w+') as s:
            s.write(bash_script)
            s.write(f'sudo {self.__name.split(".")[0]}')
        time.sleep(0.2)
        os.system("chmod 777 /writable/root/auto_start_setup.sh")
        time.sleep(0.2)
        if not os.path.exists(dst_auto):
            shutil.copyfile(src_auto, dst_auto)
            if os.path.exists(src_auto):
                os.remove(src_auto)
            os.system(r'chmod 777 {}'.format(dst_auto))
            time.sleep(1)
            os.system("ln -s {} {}".format(dst_auto, dst_wants))
        return True

    def __add_wes_script_startup(self):
        script_name = '{}.exe'.format(os.path.splitext(os.path.basename(self.__name))[0])
        file_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup'
        # items = OSTool.get_folder_items(file_path)
        # for i in items:
        #     log.info("find {} in startup folder".format(i))
        #     os.remove(file_path + r"\{}".format(i))
        cmd = r'mklink "{}\{}" "{}"'.format(file_path, script_name, self.__name)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                             shell=True)
        rs = p.stdout.readlines()
        if rs:
            result = [i.decode('utf-8') for i in rs]
        else:
            result = ['no feed back']
        log.debug('[common-function][add wes startup]mklink result {}'.format('\n'.join(result)))
        if not os.path.exists(os.path.join(file_path, script_name)):
            print('-----not exist {}'.format(os.path.join(file_path, script_name)))
            self.__create_shortcuts(self.__name, script_name)
            time.sleep(2)
            shutil.copy(f'{get_current_dir(os.path.basename(self.__name))}.lnk', file_path)
            time.sleep(1)
            if os.path.exists(file_path + '/' + '{}'.format(script_name + '.lnk')):
                log.info('add {} to startup success'.format(file_path + '/' + '{}'.format(script_name + '.lnk')))
            else:
                log.info('add to startup Fail')
                return False
        return True

    def is_auto_start(self):
        if 'window' in OS.lower():
            if os.path.exists(r'C:\ProgramData\Microsoft\Windows\Start'
                              r' Menu\Programs\Startup\{}'.format(os.path.basename(self.__name))):
                return True
            else:
                return False
        else:
            log.info('{} linux is auto start'.format(os.path.exists(self.__name)))
            if os.path.exists(self.__name):
                return True
            else:
                return False


def case_steps_run_control(steps_list, name, *args, **kwargs):
    temp_folder = get_current_dir('Test_Report', 'temp')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    case_steps_file = get_current_dir('Test_Report', 'temp', '{}.yaml'.format(name.split('.')[-1]))
    if not os.path.exists(case_steps_file) or all([os.path.exists(case_steps_file),
                                                   isinstance(YamlOperator(case_steps_file).read(), str)]):
        new_list = []
        for s in steps_list:
            step_dict = dict()
            step_dict[s] = "Norun"
            new_list.append(step_dict)
        steps_yml = YamlOperator(case_steps_file)
        steps_yml.write(new_list)
        time.sleep(5)

    steps_yml = YamlOperator(case_steps_file)
    suite_rs = False
    while True:
        new_list2 = steps_yml.read()
        log.info('original step list:')
        log.info(new_list2)
        for step in new_list2:
            step_name, step_status = list(step.items())[0]
            if step_status.upper() == 'NORUN':
                step[step_name] = 'Finished'
                log.info('current step list:')
                log.info(new_list2)
                steps_yml.write(new_list2)
                result = getattr(sys.modules[name], step_name)(*args, **kwargs)
                log.info('current step: {}'.format(step_name))
                log.info('step result: {}'.format(str(result)))
                break
        else:
            break
        if result is False:
            suite_rs = False
            break
        else:
            suite_rs = True
    return suite_rs
