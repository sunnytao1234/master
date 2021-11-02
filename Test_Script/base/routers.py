# -*- coding: utf-8 -*-
# @time     :   4/20/2021 10:12 AM
# @author   :   balance
# @file     :   routers.py
import time
from abc import ABCMeta, abstractmethod

from Common.common_function import OS

if OS == 'Windows':
    import uiautomation as uiauto
    from selenium.webdriver import Edge

from Common.common import get_current_dir, get_ui_item
from Common.common import log


class Router(metaclass=ABCMeta):
    def __init__(self, wifi_name: str = '', wifi_password: str = '',
                 web_driver=None, web_driver_path: str = None):
        """

        """

        self.__wifi_name = wifi_name
        self.__wifi_password = wifi_password

        self.__web_driver = web_driver
        self.__web_driver_path = web_driver_path

    def init_web_driver(self):
        self.web_driver = self.__web_driver(self.__web_driver_path)
        return self.web_driver

    @staticmethod
    def wait_load_time(wait_load_second: int = 5):
        time.sleep(wait_load_second)

    @abstractmethod
    def login(self, url: str, web_name: str, web_password: str) -> bool:
        """

        """
        pass

    @abstractmethod
    def set_config(self, config: dict) -> bool:
        """

        """
        pass

    @abstractmethod
    def save_config(self) -> bool:
        """

        """
        pass

    @abstractmethod
    def set_band(self, select_band: str, **depend_kargs):
        """

        """
        pass

    @abstractmethod
    def set_wireless_mode(self, select_mode: str, **depend_kargs):
        """

        """
        pass

    @abstractmethod
    def set_bandwidth(self, select_bandwidth: str, **depend_kargs):
        """

        """
        pass

    @abstractmethod
    def set_channel(self, select_channel: str, **depend_kargs):
        """

        """
        pass

    @abstractmethod
    def close(self) -> bool:
        """

        """
        pass


class AsuxAc87u(Router):
    def __init__(self, wifi_name: str, wifi_password: str,
                 web_driver=Edge,
                 web_driver_path: str = get_current_dir('Test_Utility', 'msedgedriver.exe')):
        super().__init__(wifi_name, wifi_password, web_driver, web_driver_path)

    def login(self, url: str, web_name: str, web_password: str) -> bool:
        finish_flag = False

        try:
            self.web_driver.maximize_window()
            self.web_driver.get(url)

            # 5s, wait to load web
            self.wait_load_time()

            login_name = self.web_driver.find_element_by_id("login_username")
            login_name.send_keys(web_name)

            login_password = self.web_driver.find_element_by_name("login_passwd")
            login_password.send_keys(web_password)

            signin_button = self.web_driver.find_element_by_class_name("button")
            signin_button.click()

            self.wait_load_time()
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAc87u][login] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def close(self) -> bool:
        finish_flag = False

        try:
            self.web_driver.quit()
            self.wait_load_time(3)
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAc87u][close] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def set_config(self, config: dict,
                   config_url: str = r"http://router.asus.com/Advanced_Wireless_Content.asp") -> bool:
        finish_flag = False

        try:
            self.web_driver.get(config_url)

            self.wait_load_time()

            self.set_band(select_band=config['band'])
            self.set_wireless_mode(select_mode=config['wireless_mode'], **config)
            self.set_bandwidth(select_bandwidth=config['bandwidth'], **config)
            self.set_channel(select_channel=config['channel'], **config)

            log.info(f"[AsuxAc87u][set_config] current config to set:{config}")

            self.wait_load_time()
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAc87u][set_config] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def save_config(self) -> bool:
        finish_flag = False

        try:
            apply_button = self.web_driver.find_element_by_id("applyButton")
            apply_button.click()

            self.wait_load_time(15)
            log.info(f"[AsuxAc87u][save_config] save current config")
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAc87u][save_config] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def set_band(self, select_band: str, **depend_kargs):
        if select_band == '2.4g':
            option_2g = self.web_driver.find_element_by_id("elliptic_ssid_2g")
            option_2g.click()
            self.wait_load_time(3)

        elif select_band == '5g':
            option_5g = self.web_driver.find_element_by_id("elliptic_ssid_5g")
            option_5g.click()
            self.wait_load_time(3)

        else:
            raise ValueError(f"This band<{select_band}> is not supported")

    def set_wireless_mode(self, select_mode: str, **depend_kargs):
        # depend_band = depend_kargs.get('band')

        wireless_mode = self.web_driver.find_element_by_name("wl_nmode_x")
        wireless_mode_options = wireless_mode.find_elements_by_tag_name('option')

        # if depend_band == '2.4g':
        #     pass
        #
        # elif depend_band == '5g':
        #     pass
        #
        # else:
        #     raise ValueError(f"This depend band<{depend_band}> is not supported")

        # N only mode
        if select_mode == '802.11n':
            wireless_mode_options[1].click()

        # auto mode
        elif select_mode == '802.11ac':
            wireless_mode_options[0].click()

        else:
            raise ValueError(f"This wireless mode<{select_mode}> is not supported")

    def set_bandwidth(self, select_bandwidth: str, **depend_kargs):
        depend_band = depend_kargs.get('band')
        depend_mode = depend_kargs.get('wireless_mode')

        bandwidth = self.web_driver.find_element_by_name("wl_bw")
        bandwidth_options = bandwidth.find_elements_by_tag_name('option')

        if depend_band == '2.4g':
            # N only mode
            if depend_mode == '802.11n':
                if select_bandwidth == '20/40':
                    bandwidth_options[0].click()

                elif select_bandwidth == '20':
                    bandwidth_options[1].click()

                elif select_bandwidth == '40':
                    bandwidth_options[2].click()

                else:
                    raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")

            # elif depend_mode == '802.11ac':
            #     pass

            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        elif depend_band == '5g':
            # N only mode
            if depend_mode == '802.11n':
                if select_bandwidth == '20':
                    bandwidth_options[0].click()

                elif select_bandwidth == '40':
                    bandwidth_options[1].click()

                else:
                    raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")
            # auto mode
            elif depend_mode == '802.11ac':
                if select_bandwidth == '20':
                    bandwidth_options[0].click()

                elif select_bandwidth == '40':
                    bandwidth_options[1].click()

                elif select_bandwidth == '80':
                    bandwidth_options[2].click()

                else:
                    raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")

            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        else:
            raise ValueError(f"This depend band<{depend_band}> is not supported")

    def set_channel(self, select_channel: str, **depend_kargs):
        depend_band = depend_kargs.get('band')
        depend_mode = depend_kargs.get('wireless_mode')
        # depend_bandwidth = depend_kargs.get('bandwidth')

        channel = self.web_driver.find_element_by_name("wl_channel")
        channel_options = channel.find_elements_by_tag_name('option')

        if depend_band == '2.4g':
            if depend_mode == '802.11n':
                # if depend_bandwidth == '20/40':
                #     pass
                #
                # elif depend_bandwidth == '20':
                #     pass
                #
                # elif depend_bandwidth == '40':
                #     pass
                #
                # else:
                #     raise ValueError(f"This depend bandwidth<{depend_bandwidth}> is not supported")

                # elif depend_mode == '802.11ac':
                #     pass
                if select_channel == '3':
                    channel_options[3].click()
                elif select_channel == '11':
                    channel_options[11].click()
                else:
                    raise ValueError(f"This select channel<{select_channel}> is not supported")

            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        elif depend_band == '5g':
            if depend_mode == '802.11n':
                # if depend_bandwidth == '20':
                #     channel_options[0].click()
                #
                # elif depend_bandwidth == '40':
                #     channel_options[1].click()
                #
                # else:
                #     raise ValueError(f"This depend bandwidth<{depend_bandwidth}> is not supported")

                if select_channel == '153':
                    channel_options[2].click()

                elif select_channel == '157':
                    channel_options[3].click()

                else:
                    raise ValueError(f"This select channel<{select_channel}> is not supported")

            elif depend_mode == '802.11ac':
                # if select_bandwidth == '20':
                #     bandwidth_options[0].click()
                #
                # elif select_bandwidth == '40':
                #     bandwidth_options[1].click()
                #
                # elif select_bandwidth == '80':
                #     bandwidth_options[2].click()
                #
                # else:
                #     raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")

                if select_channel == '153':
                    channel_options[2].click()

                elif select_channel == '157':
                    channel_options[3].click()

                else:
                    raise ValueError(f"This select channel<{select_channel}> is not supported")
            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        else:
            raise ValueError(f"This depend band<{depend_band}> is not supported")


class AsuxAx92u(Router):
    def __init__(self, wifi_name: str, wifi_password: str,
                 web_driver=Edge,
                 web_driver_path: str = get_current_dir('Test_Utility', 'msedgedriver.exe')):
        super().__init__(wifi_name, wifi_password, web_driver, web_driver_path)

    def login(self, url: str, web_name: str, web_password: str) -> bool:
        finish_flag = False

        try:
            self.web_driver.maximize_window()
            self.web_driver.get(url)

            self.wait_load_time()

            if "error" in (item.lower() for item in self.web_driver.title.split(" ")):
                go_button = self.web_driver.find_element_by_id("wanLink")
                go_button.click()

            login_name = self.web_driver.find_element_by_id("login_username")
            login_name.send_keys(web_name)

            login_password = self.web_driver.find_element_by_name("login_passwd")
            login_password.send_keys(web_password)

            signin_button = self.web_driver.find_element_by_class_name("button")
            signin_button.click()

            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAx92u][login] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def close(self) -> bool:
        finish_flag = False

        try:
            self.web_driver.quit()
            self.wait_load_time(3)
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAx92u][close] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def set_config(self, config: dict,
                   config_url: str = r"http://router.asus.com/Advanced_Wireless_Content.asp") -> bool:
        finish_flag = False

        try:
            self.web_driver.get(config_url)

            self.wait_load_time()

            self.set_band(select_band=config['band'])
            self.set_wireless_mode(select_mode=config['wireless_mode'], **config)
            self.set_bandwidth(select_bandwidth=config['bandwidth'], **config)
            self.set_channel(select_channel=config['channel'], **config)

            log.info(f"[AsuxAx92u][set_config] current config to set:{config}")

            self.wait_load_time()
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAx92u][set_config] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def save_config(self) -> bool:
        finish_flag = False

        try:
            apply_button = self.web_driver.find_element_by_id("applyButton")
            apply_button.click()

            self.wait_load_time(10)
            log.info(f"[AsuxAx92u][save_config] save current config")
            finish_flag = True

        except Exception:
            import traceback
            log.error(f"[AsuxAx92u][save_config] {traceback.format_exc()}")

            finish_flag = False

        finally:
            return finish_flag

    def set_band(self, select_band: str, **depend_kargs):
        if select_band == '2.4g':
            option_2g = self.web_driver.find_element_by_id("elliptic_ssid_2g")
            option_2g.click()
            self.wait_load_time(3)

        elif select_band == '5g-1':
            option_5g = self.web_driver.find_element_by_id("elliptic_ssid_5g")
            option_5g.click()
            self.wait_load_time(3)

        elif select_band == '5g-2':
            option_5g = self.web_driver.find_element_by_id("elliptic_ssid_5g_2")
            option_5g.click()
            self.wait_load_time(3)

        else:
            raise ValueError(f"This band<{select_band}> is not supported")

    def set_wireless_mode(self, select_mode: str, **depend_kargs):
        depend_band = depend_kargs.get('band')

        wireless_mode = self.web_driver.find_element_by_name('wl_nmode_x')
        wireless_mode_options = wireless_mode.find_elements_by_tag_name('option')

        if depend_band == '5g-2':
            if select_mode == '802.11ax':
                wireless_mode_options[1].click()
            else:
                raise ValueError(f"This select mode<{select_mode}> is not supported")

        else:
            raise ValueError(f"This depend band<{depend_band}> is not supported")

    def set_bandwidth(self, select_bandwidth: str, **depend_kargs):
        depend_band = depend_kargs.get('band')
        depend_mode = depend_kargs.get('wireless_mode')

        bandwidth = self.web_driver.find_element_by_name("wl_bw")
        bandwidth_options = bandwidth.find_elements_by_tag_name("option")

        if depend_band == '5g-2':
            if depend_mode == '802.11ax':
                if select_bandwidth == '20':
                    bandwidth_options[1].click()

                elif select_bandwidth == '40':
                    bandwidth_options[2].click()

                elif select_bandwidth == '80':
                    bandwidth_options[3].click()

                elif select_bandwidth == '160':
                    enable_160mhz = self.web_driver.find_element_by_id("enable_160mhz")

                    # enable 160mhz
                    if not enable_160mhz.is_selected():
                        enable_160mhz.click()

                    bandwidth_options = bandwidth.find_elements_by_tag_name("option")
                    bandwidth_options[4].click()

                else:
                    raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")

            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        else:
            raise ValueError(f"This depend band<{depend_band}> is not supported")

    def set_channel(self, select_channel: str, **depend_kargs):
        depend_band = depend_kargs.get('band')
        depend_mode = depend_kargs.get('wireless_mode')
        depend_bandwidth = depend_kargs.get('bandwidth')

        channel = self.web_driver.find_element_by_name("wl_channel")
        channel_options = channel.find_elements_by_tag_name('option')

        if depend_band == '5g-2':
            if depend_mode == '802.11ax':
                if depend_bandwidth == '20':
                    if select_channel == '157':
                        channel_options[-3].click()
                    else:
                        raise ValueError(f"This  select channel<{select_channel}> is not supported")

                elif depend_bandwidth == '40':
                    if select_channel == '157':
                        channel_options[-2].click()
                    else:
                        raise ValueError(f"This  select channel<{select_channel}> is not supported")

                elif depend_bandwidth == '80':
                    if select_channel == '157':
                        channel_options[-2].click()
                    else:
                        raise ValueError(f"This  select channel<{select_channel}> is not supported")

                elif depend_bandwidth == '160':
                    if select_channel == '128':
                        channel_options[-1].click()
                    else:
                        raise ValueError(f"This  select channel<{select_channel}> is not supported")

                else:
                    raise ValueError(f"This depend bandwidth<{depend_bandwidth}> is not supported")

            else:
                raise ValueError(f"This depend mode<{depend_mode}> is not supported")

        else:
            raise ValueError(f"This depend band<{depend_band}> is not supported")


class NetgearAx80(Router):
    def __init__(self, wifi_name: str, wifi_password: str,
                 web_driver=Edge,
                 web_driver_path: str = get_current_dir('Test_Utility', 'msedgedriver.exe')):
        super().__init__(wifi_name, wifi_password, web_driver, web_driver_path)

    def login(self, url: str, web_name: str, web_password: str) -> bool:
        finish_flag = False
        try:
            self.web_driver.maximize_window()
            self.web_driver.get(url)

            self.wait_load_time()

            login_dialog = get_ui_item(uiauto.PaneControl, name="Sign in to access this site", search_depth=3)

            login_name = get_ui_item(login_dialog.EditControl, name="Username", search_depth=7, search_wait=3)
            login_name.SetValue(web_name)

            login_password = get_ui_item(login_dialog.EditControl, name="Password", search_depth=7, search_wait=3)
            login_password.SetValue(web_password)

            login_button = get_ui_item(login_dialog.ButtonControl, name="Sign in", search_depth=7, search_wait=3)
            login_button.Click()

            self.wait_load_time()
            finish_flag = True

        except Exception:
            import traceback

            log.error(f"[NetgearAx80][login] {traceback.format_exc()}")
            finish_flag = False

        finally:
            return finish_flag

    def close(self) -> bool:
        finish_flag = False
        try:
            self.web_driver.quit()
            self.wait_load_time(3)
            finish_flag = True

        except Exception:
            import traceback

            log.error(f"[NetgearAx80][close] {traceback.format_exc()}")
            finish_flag = False

        finally:
            return finish_flag

    def set_config(self, config: dict,
                   config_url: str = r"http://www.routerlogin.net/WLG_wireless_dual_band_r10.htm") -> bool:
        finish_flag = False

        try:
            self.web_driver.get(config_url)

            self.wait_load_time()

            self.set_band(select_band=config['band'])
            self.set_wireless_mode(select_mode=config['wireless_mode'], **config)
            self.set_bandwidth(select_bandwidth=config['bandwidth'], **config)
            self.set_channel(select_channel=config['channel'], **config)

            log.info(f"[NetgearAx80][set_config] current config to set:{config}")

            self.wait_load_time()
            finish_flag = True

        except Exception:
            import traceback

            log.error(f"[NetgearAx80][set_config] {traceback.format_exc()}")
            finish_flag = False

        finally:
            return finish_flag

    def save_config(self) -> bool:
        finish_flag = False

        try:
            apply_button = self.web_driver.find_element_by_id("applyBtn")
            apply_button.click()

            self.wait_load_time(30)
            log.info(f"[NetgearAx80][save_config] save current config")
            finish_flag = True

        except Exception:
            import traceback

            log.error(f"[NetgearAx80][set_config] {traceback.format_exc()}")
            finish_flag = False

        finally:
            return finish_flag

    def set_band(self, select_band: str, **depend_kargs):
        pass

    def set_wireless_mode(self, select_mode: str, **depend_kargs):
        pass

    def set_bandwidth(self, select_bandwidth: str, **depend_kargs):
        if select_bandwidth == '20/40':
            enable_20and40 = self.web_driver.find_element_by_name("enable_coexistence")

            if not enable_20and40.is_selected():
                enable_20and40.click()

        else:
            raise ValueError(f"This select bandwidth<{select_bandwidth}> is not supported")

    def set_channel(self, select_channel: str, **depend_kargs):

        channel = self.web_driver.find_element_by_name("w_channel")
        channel_options = channel.find_elements_by_tag_name("option")

        channel_options[int(select_channel)].click()
