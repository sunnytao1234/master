import os
import re
import subprocess
import time

from Common.common_function import OSTool
from Common.file_operator import YamlOperator
from Common.log import log
from Common.common import NetWorkDisableEnable
from Common.common import get_element, run_power_shell


def run_command(commands: str, timeout: int = 15):
    log.info(f"[wireless][run_command]start run command: {commands}")

    result = subprocess.Popen(commands, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              shell=True)
    output, error = result.communicate(timeout=timeout)

    temp = output, error
    log.info(f"[wireless][run_command]finish run command: {temp}")

    return output.decode('utf-8')


class WlanLinux:
    def __init__(self, ssid: str, password: str):
        log.info(f"[WlanLinux][init]ssid:{ssid} password:{password}")

        self.ssid = ssid
        self.pwd = password

    def enable_wlan(self) -> bool:
        subprocess.Popen('mclient --quiet set root/Network/Wireless/EnableWireless 1 && mclient commit', shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.info(f"[WlanLinux][enable_wlan]enable wlan")

        value = subprocess.Popen("mclient --quiet get root/Network/Wireless/EnableWireless", shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.info(f"[WlanLinux][enable_wlan]get wlan status:{value}")

        s = value.stdout.read().decode()

        if str(s[0]) == '1':
            return True
        else:
            return False

    def check_wlan_name(self) -> bool:
        network_card = subprocess.getoutput("ifconfig -a")
        log.info("[WlanLinux][check_wlan_name]network_card value:\n{}\n".format(network_card))

        if 'wlan' in network_card:
            log.info(f"[WlanLinux][check_wlan_name]find wlan device successfully")

            return True
        else:
            log.warning(f"[WlanLinux][check_wlan_name]find wlan device unsuccessfully")

            return False

    @staticmethod
    def active_wlan():
        subprocess.getoutput('ifconfig wlan0 up')

        log.info(f"[WlanLinux][active_wlan]active wlan0")

    def scanning_ap(self):
        essid = subprocess.getoutput("sudo iwlist wlan0 scanning | grep -i essid")

        ssid_list = []
        for i in essid.split():
            ssid = re.findall('"(.*)"', i)
            if ssid == []:
                log.warning("[WlanLinux][scanning_ap]ssid value:{}".format(ssid))
            else:
                ssid_list.append(ssid[0])
                log.info('[wlanLinux][scanning_ap] ssid[0] value:{}'.format(ssid[0]))

        if len(ssid_list) == 0:
            log.warning("[WlanLinux][scanning_ap]cannot find any ssid")

        return ssid_list

    def check_ssid_in_list(self):
        ssid = self.ssid
        ssid_list = self.scanning_ap()

        if ssid in ssid_list:
            log.info(f"[WlanLinux][check_ssid_in_list]ssid<{ssid}> exists in {ssid_list}")

            return True

        else:
            log.warning(f"[WlanLinux][check_ssid_in_list]cannot find ssid<{ssid}> about this wlan,please check router")

            return False

    def add_wlan_conf(self):
        cmd = 'wpa_passphrase {ssid} {pwd} > /etc/{ssid}.conf'.format(ssid=self.ssid, pwd=self.pwd)
        subprocess.getoutput(cmd)

        log.info("[WlanLinux][add_wlan_conf]cmd value:\n{}\n".format(cmd))
        value = subprocess.getoutput('cat /etc/{ssid}.conf'.format(ssid=self.ssid))
        log.info('[WlanLinux][add_wlan_conf]get add_wlan_conf result:{}'.format(value))

        if self.ssid and self.pwd in value:
            log.info("[WlanLinux][add_wlan_conf]add wlan config successfully")
            return True
        else:
            log.warning("[WlanLinux][add_wlan_conf]add wlan config unsuccessfully")
            return False

    def connect_wireless(self):
        log.info('[wlanlinux][connect_wireless] self ssid value:{}'.format(self.ssid))
        if self.ssid in ['AsuxAx92u_5G-2', 'AsuxAc87u', 'NetgearAx80']:
            time.sleep(10)
            return True
        else:
            self.del_wireless_profile_from_reg()
            self.disable_wlan()
            time.sleep(10)
            self.enable_wlan()
            time.sleep(60)
            self.add_wlan_conf()
            cmd = 'wpa_supplicant -i wlan0 -c /etc/{ssid}.conf -B'.format(ssid=self.ssid)

            log.info("[WlanLinux][connect_wireless]cmd value:\n{}\n".format(cmd))

            connect_result = subprocess.getoutput(cmd)
            log.info('[WlanLinux][connect_wireless]get connect result:{}'.format(connect_result))

            if 'Successfully' in connect_result:
                log.info("[WlanLinux][connect_wireless]connect wireless successfully")
            else:
                log.error("[WlanLinux][connect_wireless]connect wireless unsuccessfully")

            subprocess.getoutput('dhclient wlan0')

            cat_connect = subprocess.getoutput('ifconfig')
            log.info("[WlanLinux][connect_wireless]get connect result:{}".format(cat_connect))

            if '192.168.' in cat_connect:
                log.info("[WlanLinux][connect_wireless]identify ip successfully")

                return True
            else:
                log.warning("[WlanLinux][connect_wireless]]identify ip unsuccessfully")

                return False

    def access_internet(self, ip: str = "192.168.1.1", ping_cnt: int = 1):
        result = subprocess.getoutput(f'ping {ip} -c {ping_cnt}')

        if 'host unreachable' in result or '100% loss' in result:
            log.warning("[WlanLinux][access_internet]not access internet unsuccessfully")

            return False
        else:
            log.info("[WlanLinux][access_internet]access internet successfully")

            return True

    def disable_wlan(self):
        subprocess.Popen('mclient --quiet set root/Network/Wireless/EnableWireless 0 && mclient commit', shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.info(f"[WlanLinux][disable_wlan]disable wlan")

        value = subprocess.Popen("mclient --quiet get root/Network/Wireless/EnableWireless", shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.info(f"[WlanLinux][disable_wlan]get wlan status:{value}")

        s = value.stdout.read().decode()

        if str(s[0]) == ' ':
            return True
        else:
            return False

    def del_wireless_profile_from_reg(self):
        profiles = subprocess.getoutput("mclient --quiet get root/Network/Wireless/Profiles").splitlines()
        log.info('[wlanlinux][del_wireless_profile_from_reg] profiles:{}'.format(profiles))

        if profiles:
            log.info('[wlanlinux][del_wireless_profile_from_reg]found wireless profile')

            for profile in profiles:
                profile_name = profile.split('/')[-1].strip()
                log.info("[wlanlinux][del_wireless_profile_from_reg] profile_name:{}".format(profile_name))

                os.system('mclient delete root/Network/Wireless/Profiles/{}'.format(profile_name))
                os.system('mclient commit root/Network/Wireless')

            if not subprocess.getoutput("mclient --quiet get root/Network/Wireless/Profiles").splitlines():
                log.info("[wlanlinux][del_wireless_profile_from_reg]delete all wireless profiles success")

                return True
            else:
                log.info("[wlanlinux][del_wireless_profile_from_reg]delete all wireless profiles fail")

                return False
        else:
            log.info("current no wireless profiles")
            return False

    def reset_env(self, cycle_number=60, wait_time=5):
        if self.ssid in ['AsuxAx92u_5G-2', 'AsuxAc87u', 'NetgearAx80']:
            time.sleep(10)
            return True
        else:
            delete_conf = OSTool.get_current_dir('/etc', '{}.conf'.format(self.ssid))
            if os.path.exists(delete_conf):
                os.remove(delete_conf)
            time.sleep(10)

            log.info(f'[wlanlinux][reser_env]%{self.ssid}')
            if self.ssid in ['AsuxAc87u', 'AsuxAc87u_5G']:
                self.ssid = 'AsuxAc87u'
                self.pwd = 'AsuxAc87u'
            elif self.ssid in ['AsuxAx92u_5G-2', 'AsuxAx92u', 'AsuxAx92u_5G-1']:
                self.ssid = 'AsuxAx92u'
                self.pwd = 'AsuxAx92u'
            elif self.ssid in ['NetgearAx80', 'NetgearAx80_5g']:
                self.ssid = 'NetgearAx80'
                self.pwd = 'NetgearAx80'

            self.disable_wlan()
            time.sleep(15)
            self.enable_wlan()
            time.sleep(15)

            add_profile_cmd = 'wpa_passphrase {ssid} {pwd} > /etc/{ssid}.conf'.format(ssid=self.ssid, pwd=self.pwd)
            subprocess.getoutput(add_profile_cmd)

            log.info("[WlanLinux][add_wlan_conf]cmd value:\n{}\n".format(add_profile_cmd))
            connect_cmd = 'wpa_supplicant -i wlan0 -c /etc/{ssid}.conf -B'.format(ssid=self.ssid)

            log.info("[WlanLinux][connect_wireless]cmd value:\n{}\n".format(connect_cmd))
            subprocess.getoutput(connect_cmd)
            for i in range(cycle_number):
                s = subprocess.getoutput("iwconfig wlan0 | grep SSID")
                pattern = re.compile('"(.*)"')
                ssid_list = pattern.findall(s)
                if len(ssid_list) == 1:
                    ssid = ssid_list[0]
                    log.info('[wlanlinux][reset_env]ssid value:{}'.format(ssid))
                    if ssid == self.ssid:
                        log.info('[wlanLinux][reset_env] reset_env successful and current wifi is:{}'.format(ssid))
                        return True
                    else:
                        log.error('ssid value are different {}'.format(self.ssid))
                        return False
                else:
                    time.sleep(wait_time)
                    continue
            log.info('Fail to connect to wireless after {} seconds.'.format(cycle_number * wait_time))
            return 'timeout'


class WlanWes:
    def __init__(self, ssid: str) -> None:
        self.ssid = ssid

        self.xml_map_file = OSTool.get_current_dir('Test_Data', 'xml', 'xml_map.yml')
        self.xml_map = YamlOperator(self.xml_map_file).read_bytes()

        self.profile_path = OSTool.get_current_dir('Test_Data', 'xml', '{}.xml'.format(self.xml_map.get(self.ssid)))

        log.info(f"[WlanWes][init]WlanWes init:{ssid}\n{self.profile_path}\n")

    def disable_lan(self):
        log.info(f"[WlanWes][disable_lan]start to disable lan")
        NetWorkDisableEnable().disable_internet()
        log.info(f"[WlanWes][disable_lan]end to disable lan")

    def check_disable_lan(self, check_cycle: int = 30, wait_time: int = 2) -> bool:
        for i in range(check_cycle):
            network_disconnect = get_element("NETEORK_DISCONNECT")

            if network_disconnect.Exists():
                log.info("[WlanWes][check_disable_lan]disable lan/wlan successfully")

                return True
            else:
                log.warning(f"[WlanWes][check_disable_lan]wait {wait_time}s to disable lan/wlan")
                time.sleep(wait_time)

                continue

        log.warning("[WlanWes][check_disable_lan]disable lan/wlan unsuccessfully")

        return False

    def enable_lan(self):
        log.info(f"[WlanWes][enable_lan]start to enable lan")
        NetWorkDisableEnable().enable_internet()
        log.info(f"[WlanWes][enable_lan]end to enable lan")

    def check_enable_lan(self, check_cycle: int = 50, wait_time: int = 10) -> bool:
        for i in range(check_cycle):
            network_sh = get_element("NETWORK_SH")

            if network_sh.Exists():
                log.info("[WlanWes][check_enable_lan]enable lan successfully")

                return True
            else:
                log.warning(f"[WlanWes][check_enable_lan]wait {wait_time}s to disable lan")
                time.sleep(wait_time)

                continue

        log.warning("[WlanWes][check_enable_lan]enable lan unsuccessfully")

        return False

    def enable_wlan(self):
        log.info(f"[WlanWes][enable_wlan]start to enable wlan")
        NetWorkDisableEnable().enable_wlan()
        log.info(f"[WlanWes][enable_wlan]end to enable wlan")

    def check_enable_wlan(self) -> bool:
        interface = subprocess.Popen("netsh interface show interface", shell=True, stderr=subprocess.STDOUT,
                                     stdout=subprocess.PIPE)

        interface_info = interface.stdout.readlines()[5]
        if 'Enabled ' in str(interface_info):
            log.info("[WlanWes][check_enable_wlan]enable wlan successfully")

            return True
        else:
            log.warning("[WlanWes][check_enable_wlan]enable wlan unsuccessfully")

            return False

    def disable_wlan(self):
        log.info(f"[WlanWes][disable_wlan]start to disable wlan")
        NetWorkDisableEnable().disable_wlan()
        log.info(f"[WlanWes][disable_wlan]end to disable wlan")

    def check_disable_wlan(self):
        log.info(f"[WlanWes][check_disable_wlan]start to check disable wlan")
        self.check_disable_lan()
        log.info(f"[WlanWes][check_disable_wlan]end to check disable wlan")

    def check_client_exists_profile(self):
        profile_list = []

        check_profile = subprocess.getoutput('netsh wlan show profile')
        log.info('[Wlanwes][check_client_exists_profile] check_profile value is:{}'.format(check_profile))

        if 'All User Profile     :' not in check_profile:
            log.warning("[wlan wes][check_client_exists_profile]this uut not exists profile")
            profile_list = None
        else:
            profile_list_value = check_profile.strip().replace('\n', '').split('User Profiles')[0].split(
                'All User Profile     :')[1:]

            for data in profile_list_value:
                value = data.replace(' ', '')
                profile_list.append(value)
        return profile_list

    def scanning_visible_wifi(self):
        result = subprocess.Popen('netsh wlan show networks', shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)

        result_value = result.stdout.readlines()
        result_value_list = result_value[4::5]

        length = len(result_value_list)

        ssid_list = []
        for i in range(length - 1):
            if 'SSID' in result_value_list[i].decode():
                data = result_value_list[i].decode().strip().split(':')[1]

                log.info(f"[WlanWes][scanning_visible_wifi]add new ssid:{data}")

                ssid_list.append(data)

        if len(ssid_list) == 0:
            log.warning(f"[WlanWes][scanning_visible_wifi]ssid list has no new ssid")

        return ssid_list

    def add_profile(self) -> bool:
        value = run_power_shell("netsh wlan add profile filename={}".format(self.profile_path))
        log.info(f"[WlanWes][add_profile]netsh wlan add profile filename={self.profile_path}")

        if 'added' in value:
            log.info(f"[WlanWes][add_profile]add profile{self.profile_path} successfully")

            return True
        else:
            log.warning(f"[WlanWes][add_profile]add profile{self.profile_path} unsuccessfully")

            return False

    def delete_profile(self) -> bool:
        log.info('[WlanWes][delete_profile]delete {} profile from interface'.format(self.ssid))
        check_result = run_power_shell("netsh wlan delete profile name={}".format(self.ssid))
        log.info('[WlanWes][delete_profile] check_result value is:{}'.format(check_result))

        if 'deleted' in check_result:
            log.info("[WlanWes][delete_profile]delete profile successfully")

            return True
        else:
            log.warning("[WlanWes][delete_profile]delete profile unsuccessfully")

            return False

    def connect_wifi(self):
        self.disconnect()
        alerady_profile = self.check_client_exists_profile()
        ssid = self.ssid

        if alerady_profile is not None and ssid in alerady_profile:
            run_power_shell('netsh wlan connect name={}'.format(self.ssid)).strip()

            log.info(f"[WlanWes][connect_wifi]run cmd:set profileparameter name={ssid} connectionmode=auto")

        else:
            if self.add_profile():
                t = run_power_shell('netsh wlan connect name={}'.format(self.ssid)).strip()
                log.info(f"[WlanWes][connect_wifi]run cmd:netsh wlan connect name={self.ssid}")

                log.info(f"[WlanWes][connect_wifi]run cmd result:{t}")

                time.sleep(5)

    def check_connect_result(self, cycle: int = 30) -> bool:
        for i in range(cycle):
            wifi = get_element('WIRELESS')

            if self.ssid == wifi.AccessibleCurrentName():
                log.info(f"[WlanWes][check_connect_result]connect {self.ssid} successfully")

                return True
            else:
                log.info(f"[WlanWes][check_connect_result]connect {self.ssid} unsuccessfully")

                return False

    def disconnect(self):
        log.info("[WlanWes][disconnect]disconnect wlan")

        run_power_shell('netsh wlan disconnect')
        log.info(f"[WlanWes][disconnect]run cmd:netsh wlan disconnect")

    def change_wifi_switch(self, action: str = '', wait_time: int = 5):
        setting_window = get_element('SETTING_WINDOWS')
        wifi = get_element("WI_FI")
        wifi_switch_button = get_element("WIFI_SWITCH")
        close_setting = get_element("WIFI_CLOSE")

        log.info(f"[WlanWes][change_wifi_switch]run cmd:start ms-settings:network")
        subprocess.call("start ms-settings:network", shell=True)

        if setting_window.Exists():
            log.info('[WlanWes][change_wifi_switch]open setting window successfully')

            if wifi.Exists():
                wifi.Click()
                time.sleep(wait_time)

        if action.upper() == 'OPEN':
            if wifi_switch_button.CurrentToggleState() == 1:
                log.info("[WlanWes][change_wifi_switch]The wifi hardware switch is turned on")

            else:
                wifi_switch_button.Click()
                log.info("[WlanWes][change_wifi_switch]open wifi hardware switch successfully")

            time.sleep(wait_time)
            close_setting.Click()

            return True

        elif action.upper() == 'CLOSE':
            if wifi_switch_button.CurrentToggleState() == 0:
                log.info("[WlanWes][change_wifi_switch]the wifi hardware switch is off")
            else:
                wifi_switch_button.Click()
                log.info("[WlanWes][change_wifi_switch]close wifi hardware switch successfully")

            time.sleep(wait_time)
            close_setting.Click()

            return True
        else:
            log.error(f"[WlanWes][change_wifi_switch]input action:{action} is not supported")

            return False

    def reset_env(self, wait_time: int = 60) -> bool:
        log.info('[WlanWes][reset_env]restore UUT test env')

        self.disconnect()
        self.delete_profile()

        reset_87U_path = OSTool.get_current_dir('Test_Data', 'xml', 'Wi-Fi-AsuxAc87u.xml')
        reset_92u_path = OSTool.get_current_dir('Test_Data', 'xml', 'Wi-Fi-AsuxAx92u.xml')
        reset_Ax80_path = OSTool.get_current_dir('Test_Data', 'xml', 'Wi-Fi-NetgearAx80.xml')

        log.info('[WlanWes][reset_env]current ssid value:{}'.format(self.ssid))

        if self.ssid in ['AsuxAc87u', 'AsuxAc87u_5G']:
            run_power_shell("netsh wlan add profile filename={}".format(reset_87U_path))
            self.ssid = 'AsuxAc87u'

        elif self.ssid in ['AsuxAx92u_5G-2', 'AsuxAx92u', 'AsuxAx92u_5G-1']:
            run_power_shell("netsh wlan add profile filename={}".format(reset_92u_path))
            self.ssid = 'AsuxAx92u'

        elif self.ssid in ['NetgearAx80', 'NetgearAx80_5g']:
            run_power_shell("netsh wlan add profile filename={}".format(reset_Ax80_path))
            self.ssid = 'NetgearAx80'

        run_power_shell('netsh wlan connect name={}'.format(self.ssid)).strip()
        log.info(f"[WlanWes][reset_env]run cmd:netsh wlan connect name={self.ssid}")

        time.sleep(wait_time)

        log.info('[WlanWes][reset_env] start check this current wifi name')
        check_value = subprocess.getoutput('netsh wlan show interface')
        log.info('[WlanWes][reset_env] check value：{}'.format(check_value))

        value = re.findall('.SSID.*', check_value)
        connect_wifi_name = value[0].strip().split(':')[1].strip()
        log.info('[WlanWes][reset_env]current connect wifi name:{}'.format(connect_wifi_name))

        if connect_wifi_name == self.ssid:
            log.info('[WlanWes][reset_env]reset env successfully')

            return True
        else:
            log.error('[WlanWes][reset_env]reset env unsuccessfully')

            return False
