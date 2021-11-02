# -*- coding: utf-8 -*-

import json
# Form implementation generated from reading ui file 'main_ui.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!
import os
import socket
import threading
import time
import traceback

import psutil
from PyQt5 import QtCore, QtWidgets

from Common import valve, man, camera
from Common.camera import CAMERA, check_video_exist
from Common.common import get_serial_port
from Common.common import server_iperf3_control
from Common.common_function import OSTool, get_current_dir
from Common.file_operator import YamlOperator
from Common.log import log
from Common.socket_action import SocketClient
from Test_Script.base.main_agent import BaseUI
from Test_Script.base.routers import AsuxAc87u, AsuxAx92u, NetgearAx80
from Test_Script.base.routers import Router
from Test_Script.base.socket_action import SocketClient as SClient, SocketAgent as SAgent


class UIStyleSheet:
    common = """
            QTabWidget::pane{
                border:none;
                color:white;
                border:1px solid #F3F3F5;
                border-radius:10px;
                text-align:center;
                background: transparent
                    }
            QLabel{
                border:none;
                color:black;
                border-radius:10px;
                font-size:12px;
                height:40px;
                padding-left:10px;
                padding-right:10px;
                text-align:center;
                }
            QCheckBox{
                border-radius:10px;
                font-size:12px;
                height:40px;
            }
            QPushButton{
                border:none;
                color:white;
                background:gray;
                border:1px solid #F3F3F5;
                border-radius:10px;
                font-size:12px;
                height:40px;
                padding-left:10px;
                padding-right:10px;
                text-align:center;
                }
            QPushButton:hover{
                color:black;
                border:1px solid #F3F3F5;
                border-radius:10px;
                background:LightGray;
                } 
        """
    label = """
                QLabel{
                border:none;
                color:black;
                background-color:LightGray;
                border:1px solid #F3F3F5;
                border-radius:3px;
                font-size:12px;
                height:40px;
                padding-left:10px;
                padding-right:10px;
                text-align:center;
                }
            """
    label_title = """
                    QLabel{
                    border:none;
                    color:black;
                    font-size:18px;
                    height:40px;
                    padding-left:10px;
                    padding-right:10px;
                    text-align:center;
                    }
                """


class UIMain(BaseUI):
    def __init__(self, Form):
        super().__init__(Form)
        self.sock: SocketClient = None
        self.run_test = None

        # log.info(self.frame, '------------------')
        self.setup_ui_(Form)

    def setup_ui_(self, Form):
        self.uut_ip_edit = QtWidgets.QLineEdit(self.frame)
        self.uut_ip_edit.setGeometry(QtCore.QRect(120, 20, 113, 20))
        self.uut_ip_edit.setObjectName("uut_ip_edit")
        self.uut_ip_edit.setPlaceholderText('xxx.xxx.xxx.xxx')

        self.uut_ip_label = QtWidgets.QLabel(self.frame)
        self.uut_ip_label.setGeometry(QtCore.QRect(20, 20, 71, 21))
        self.uut_ip_label.setObjectName("uut_label")

        self.btn_connect = QtWidgets.QPushButton(self.frame)
        self.btn_connect.setGeometry(QtCore.QRect(270, 20, 85, 23))
        self.btn_connect.setObjectName("connect_button")
        self.btn_connect.clicked.connect(self.connect)

        self.boot_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.boot_chkbox.setGeometry(QtCore.QRect(20, 40, 70, 17))
        self.boot_chkbox.setObjectName("boot_checkbox")

        self.boot_edit = QtWidgets.QLineEdit(self.frame_test)
        self.boot_edit.setGeometry(QtCore.QRect(120, 40, 113, 20))
        self.boot_edit.setObjectName("boot_edit")
        self.boot_edit.setEnabled(False)

        self.reboot_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.reboot_chkbox.setGeometry(QtCore.QRect(20, 80, 70, 17))
        self.reboot_chkbox.setObjectName("reboot_checkbox")

        self.reboot_edit = QtWidgets.QLineEdit(self.frame_test)
        self.reboot_edit.setGeometry(QtCore.QRect(120, 80, 113, 20))
        self.reboot_edit.setObjectName("reboot_edit")
        self.reboot_edit.setEnabled(False)

        self.lan_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.lan_chkbox.setGeometry(QtCore.QRect(20, 120, 70, 17))
        self.lan_chkbox.setObjectName("lan_checkbox")

        self.lan_edit = QtWidgets.QLineEdit(self.frame_test)
        self.lan_edit.setGeometry(QtCore.QRect(120, 120, 113, 20))
        self.lan_edit.setObjectName("lan_edit")
        self.lan_edit.setDisabled(True)

        self.wlan_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.wlan_chkbox.setGeometry(QtCore.QRect(20, 160, 141, 31))
        self.wlan_chkbox.setObjectName("wlan_checkbox")

        self.wlan_router_comb = QtWidgets.QComboBox(self.frame_test)
        self.wlan_router_comb.setGeometry(QtCore.QRect(120, 160, 111, 22))
        self.wlan_router_comb.setObjectName("comboBox")
        for v in self.test_item.get('router'):
            self.wlan_router_comb.addItem(v)

        self.performance_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.performance_chkbox.setGeometry(QtCore.QRect(20, 200, 141, 31))
        self.performance_chkbox.setObjectName("performance_chkbox")

        self.perfomance_comb = QtWidgets.QComboBox(self.frame_test)
        self.perfomance_comb.setGeometry(QtCore.QRect(120, 200, 111, 22))
        self.perfomance_comb.setObjectName("performance_combobox")
        for k, v in self.test_item.get('performance').items():
            self.perfomance_comb.addItem(v)
        self.perfomance_comb.setDisabled(True)

        self.storage_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.storage_chkbox.setGeometry(QtCore.QRect(20, 240, 141, 31))
        self.storage_chkbox.setObjectName("storage_checkbox")

        self.storage_comb = QtWidgets.QComboBox(self.frame_test)
        self.storage_comb.setGeometry(QtCore.QRect(120, 240, 111, 22))
        self.storage_comb.setObjectName("storage_comboBox")
        for k, v in self.test_item.get('storage').items():
            self.storage_comb.addItem(v)
        self.storage_comb.setDisabled(True)

        self.thin_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.thin_chkbox.setGeometry(QtCore.QRect(20, 280, 70, 17))
        self.thin_chkbox.setObjectName("thin_checkbox")

        self.thin_type_edit = QtWidgets.QLineEdit(self.frame_test)
        self.thin_type_edit.setGeometry(QtCore.QRect(120, 280, 113, 20))
        self.thin_type_edit.setObjectName("thin_type_edit")
        self.thin_type_edit.setEnabled(False)

        self.os_comb.setEnabled(True)

        self.retranslateUi_(Form)

        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi_(self, Form):
        _translate = QtCore.QCoreApplication.translate

        self.uut_ip_label.setText(_translate("Form", "UUT IP"))
        self.wlan_chkbox.setText(_translate("Form", "Wlan"))
        self.lan_chkbox.setText(_translate("Form", "Lan"))
        self.boot_chkbox.setText(_translate("Form", "Boot"))
        self.reboot_chkbox.setText(_translate("Form", "Reboot"))
        self.thin_chkbox.setText(_translate("Form", "Thin"))

        self.btn_connect.setText(_translate("Form", "Connect"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.test_ui), _translate("Form", "Test"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.router), _translate("Form", "UUTInfo"))

    def connect(self):
        self.sock.set_connection(self.uut_ip_edit.text(), 33333)
        if self.sock.connect():
            self.btn_connect.setText('Connected')
            self.btn_connect.setDisabled(True)
            self.btn_connect.setStyleSheet("""
                background-color:LightGreen;
            """)

            # todo:improve performance
            self.sock.send_command('echo {}>server.txt'.format(OSTool.get_ip()))
            self.fill_remote_uut_info()

    def fill_remote_uut_info(self):
        self.sock.get_socket().sendall('uut_info'.encode('utf-8'))
        result = json.loads(self.sock.get_socket().recv(10240).decode('utf-8'))

        for k, v in result.items():
            log.info(f"{k},{v}")

            try:
                self.uut_info_dict[k].setText(str(v[0].get('output')))
            except:
                log.error(traceback.print_exc())

    def watch_connection(self):
        fail_count = 0
        while 1:
            if self.sock.heartbeat():
                # self.btn_connect.setEnabled(False)
                # self.btn_connect.setText('Connected')
                time.sleep(5)
                continue
            else:
                if fail_count < 3:
                    time.sleep(5)
                    fail_count += 1
                    continue
                log.info('[UIMain][watch_connection]disconnected')
                self.btn_connect.setEnabled(True)
                self.btn_connect.setText('Connect')
                break

    def launch(self):
        source = YamlOperator(get_current_dir('Test_Data', 'td_common', 'global_config.yml')).read()

        if self.btn_connect.isEnabled():
            log.info('[UIMain][launch]not connected to agent')
            return False

        _os = self.os_comb.currentText()
        platform = self.platform_edit.text()
        tester = self.tester_edit.text()
        uut_ip = self.uut_ip_edit.text()
        with open('uut.txt', 'w') as f:
            f.write(uut_ip)
        self.btn_launch.setDisabled(True)
        self.btn_launch.setStyleSheet("""
            background-color:LightGreen;
        """)

        general_data = {'os': _os, 'platform': platform, 'tester': tester}

        # get uut information data
        for name in self.test_item.get('uut_information'):
            general_data[name] = self.uut_info_dict[name].text()

        if self.wlan_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Wlan ...')

            # check and stop old iperf server when the program exits abnormally
            iperf_server_path = OSTool.get_current_dir("Test_Utility", 'iperf3.exe')
            for proc in psutil.process_iter():
                # check whether the process name matches
                try:
                    if proc.name().lower() == "iperf3.exe":
                        log.info(
                            f"[UIMain][launch]find iperf3 process firstly before test:{proc.pid},{proc.name()}")
                        proc.kill()
                        log.info(
                            f"[UIMain][launch]kill iperf3 process successfully")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            support_routers = {
                'asux_ac87u': AsuxAc87u,
                'asux_ax92u': AsuxAx92u,
                'netgear_ax80': NetgearAx80
            }
            selected_router = self.wlan_router_comb.currentText().lower()
            support_item = self.test_item.get('router_support').get(selected_router).get('support')
            router_config = self.test_item.get('router_support').get(selected_router)
            router: Router = support_routers[selected_router](wifi_name='', wifi_password='')

            wlan_data = {'name': 'wlan',
                         'loop': self.test_item.get('test_data').get('wlan_loop'),
                         'router': self.wlan_router_comb.currentText().lower(),
                         'class_name': router_config['class_name'],
                         'total_config_count': len(support_item),
                         'network': self.test_item.get('network')}
            wlan_data.update(general_data)

            for index, item in enumerate(support_item):
                wlan_data['current_config'] = item
                wlan_data['current_config_count'] = index + 1

                log.info(f"[UIMain][launch]current test case is:{index + 1}/{len(support_item)}")

                with router.init_web_driver() as driver:
                    router.login(url=router_config['url'],
                                 web_name=router_config['web_username'],
                                 web_password=router_config['web_password'])
                    router.set_config(item)
                    router.save_config()

                log.info(f"[UIMain][launch]wait to reconnect to the router:{selected_router}")

                # check and start new iperf server
                os.popen('{} -s'.format(iperf_server_path))
                time.sleep(15)  # wait 15s to open the iperf process
                for proc in psutil.process_iter():
                    # check whether the process name matches
                    try:
                        if proc.name().lower() == "iperf3.exe":
                            log.info(f"[UIMain][launch]run iperf3 successfully")
                            break

                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                self.launch_test(wlan_data)
                self.wlan_chkbox.setCheckState(QtCore.Qt.Unchecked)
                log.info("[UIMain][launch]launch test successfully")

                # check and stop current iperf server
                for proc in psutil.process_iter():
                    # check whether the process name matches
                    try:
                        if proc.name().lower() == "iperf3.exe":
                            log.info(
                                f"[UIMain][launch]find iperf3 process successfully:{proc.pid},{proc.name()}")
                            proc.kill()
                            log.info(
                                f"[UIMain][launch]kill iperf3 process successfully")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

        if self.lan_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Lan ...')

            threading.Thread(target=server_iperf3_control).start()

            lan_data = {'name': 'lan',
                        'loop': self.test_item.get('test_data').get('lan_loop'),
                        'network': self.test_item.get('network')}

            lan_data.update(general_data)
            self.launch_test(lan_data)
            self.lan_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.boot_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Boot ...')

            boot_data = {'name': 'boot',
                         'loop': self.test_item.get('test_data').get('boot_loop'),
                         'mac_info': self.uut_info_dict['mac_info'],
                         'boot_wait_time': source['boot']['boot_wait_time'],
                         'camera_device_index': source['boot']['camera_device_index'],
                         'manual_boot_list': source['boot']['manual_boot_list'],
                         'uut_broadcast': source['boot']['uut_broadcast'],
                         'client_ip': self.uut_ip_edit.text()
                         }
            boot_data.update(general_data)
            log.info(boot_data)

            self.launch_test(boot_data)
            self.boot_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.reboot_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Reboot ...')

            reboot_data = {'name': 'reboot',
                           'loop': self.test_item.get('test_data').get('reboot_loop'),
                           'mac_info': self.uut_info_dict['mac_info'],
                           'boot_wait_time': source['boot']['boot_wait_time'],
                           'camera_device_index': source['boot']['camera_device_index'],
                           'manual_boot_list': source['boot']['manual_boot_list'],
                           'uut_broadcast': source['boot']['uut_broadcast'],
                           'client_ip': self.uut_ip_edit.text()
                           }
            reboot_data.update(general_data)
            log.info(reboot_data)

            self.launch_test(reboot_data)
            self.boot_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.performance_chkbox.checkState() == QtCore.Qt.Checked and \
                self.storage_chkbox.checkState() == QtCore.Qt.Checked:
            try:
                self.sock.close()
            except Exception:
                log.info(f"[UIMain][launch]get exception from: {traceback.format_exc()}")
            finally:
                self.connect()

        if self.performance_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Performance ...')

            perf_data = {'name': 'performance', 'loop': self.test_item.get('test_data').get('performance_loop')}
            perf_data.update(general_data)
            self.launch_test(perf_data)
            self.performance_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.storage_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Storage ...')

            storage_data = {'name': 'storage',
                            'loop': self.test_item.get('test_data').get('storage_loop'),
                            'deviation': self.test_item.get('test_data').get('deviation')}
            storage_data.update(general_data)
            self.launch_test(storage_data)
            self.storage_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.thin_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing capture and deploy ...')

            thin_data = {'name': 'thin',
                         'loop': self.test_item.get('test_data').get('thin_loop'),
                         'mac_info': self.uut_info_dict['mac_info'].text()
                         }

            log.info('[main_ui]thin_data value:{}'.format(thin_data))
            thin_data.update(general_data)
            if os.path.exists('uut_info.txt'):
                os.remove('uut_info.txt')
            uut_info = open('uut_info.txt', 'a')
            mac_info = self.uut_info_dict['mac_info'].text()
            disk_info = self.uut_info_dict['disk_info'].text()
            os_info = self.uut_info_dict['os_info'].text()
            ml_info = self.uut_info_dict['ml_info'].text()
            uut_ip = self.uut_ip_edit.text()
            uut_platfrom = self.platform_edit.text()
            test_info = self.tester_edit.text()
            disk_pn = self.uut_info_dict['disk_pn'].text()

            if disk_pn == '':
                disk_pn = 'None'
            else:
                disk_pn = disk_pn
            uut_info.writelines(
                ['{}\n'.format(uut_ip), '{}\n'.format(uut_platfrom), '{}\n'.format(mac_info),
                 '{}\n'.format(disk_info), '{}\n'.format(os_info), '{}\n'.format(ml_info),
                 '{}\n'.format(test_info), '{}'.format(disk_pn)])
            uut_info.close()
            port_name = self.test_item.get('port').get('sending_appli_name')
            port = get_serial_port(port_name)
            log.info('get port {} from using name {}'.format(port, port_name))
            valve_instance = valve.ValveContainer(port)
            valve_instance.open()
            eye = camera.CAMERA()
            eye.show_t()
            self.launch_test(thin_data)
            self.thin_chkbox.setCheckState(QtCore.Qt.Unchecked)



    def launch_test(self, data, timeout=1200):
        log.info(f"[UIMain][launch_test]current system information: {data}")

        try:
            if 'wlan' == data['name']:
                client = SClient(server_ip=self.uut_ip_edit.text(), server_port=2333)
                conn = client.send_message(data)

                result = None

                if isinstance(conn, socket.socket):
                    server = SAgent(listen_ip='0.0.0.0', listen_port=6666)
                    server.open_server(keepalive=False)

                    for i in range(timeout):
                        if not server.res_queue.empty():
                            result = server.res_queue.get()
                            server.res_queue.task_done()
                            if len(result) != 0:
                                break
                        time.sleep(1)

                    if result == 'TEST FINISHED':
                        log.info('[UIMain][launch_test]Test {} Finished'.format(data.get('name')))

                    elif result == 'TEST FAILED':
                        log.error('[UIMain][launch_test]Test {} Failed'.format(data.get('name')))

                    server.close_server()

                    return
                else:
                    log.error("[UIMain][launch_test]cannot create socket connection")

                client.close_client()

            if 'boot' == data['name']:
                from Test_Script.boot import start as boot_start

                server = SAgent(listen_ip='0.0.0.0', listen_port=6667)
                server.open_server(keepalive=False)

                result = 'TEST FAILED'

                boot_start(data)

                for i in range(timeout):
                    if not server.res_queue.empty():
                        result = server.res_queue.get()
                        server.res_queue.task_done()

                        if len(result) != 0:
                            break

                    time.sleep(1)

                if server.close_server():
                    if result == 'TEST FINISHED':
                        log.info('[UIMain][launch_test]Test {} Finished'.format(data.get('name')))
                        return True
                    elif result == 'TEST FAILED':
                        log.error('[UIMain][launch_test]Test {} Failed'.format(data.get('name')))
                        return True

            if 'reboot' == data['name']:
                from Test_Script.reboot import start as reboot_start

                server = SAgent(listen_ip='0.0.0.0', listen_port=6667)
                server.open_server(keepalive=False)

                result = 'TEST FAILED'

                reboot_start(data)

                for i in range(timeout):
                    if not server.res_queue.empty():
                        result = server.res_queue.get()
                        server.res_queue.task_done()

                        if len(result) != 0:
                            break

                    time.sleep(1)

                if server.close_server():
                    if result == 'TEST FINISHED':
                        log.info('[UIMain][launch_test]Test {} Finished'.format(data.get('name')))
                        return True
                    elif result == 'TEST FAILED':
                        log.error('[UIMain][launch_test]Test {} Failed'.format(data.get('name')))
                        return True

            if 'thin' in data['name']:
                client = SClient(server_ip=self.uut_ip_edit.text(), server_port=2333)
                conn = client.send_message(data)

                result = None

                if isinstance(conn, socket.socket):
                    server = SAgent(listen_ip='0.0.0.0', listen_port=55555)
                    server.open_server(keepalive=False)

                    for i in range(timeout):
                        if not server.res_queue.empty():
                            result = server.res_queue.get()
                            server.res_queue.task_done()

                            if len(result) != 0:
                                break

                        time.sleep(1)

                    if result == 'TEST FINISHED':
                        log.info('[UIMain][launch_test]Test {} Finished'.format(data.get('name')))
                        self.status_bar.setText('All Test Finished')
                        camera.CAMERA().__del__()

                    elif result == 'TEST FAILED':
                        log.error('[UIMain][launch_test]Test {} Failed'.format(data.get('name')))

                    server.close_server()

                    return
                else:
                    log.error("[UIMain][launch_test]cannot create socket connection")

                client.close_client()

            if data['name'] not in ('wlan', 'boot', 'reboot', 'thin'):
                self.sock.get_socket().sendall('START_TEST'.encode('utf-8'))
                if self.sock.get_socket().recv(1024).decode('utf-8').lower() == 'accept test':
                    self.sock.get_socket().sendall(json.dumps([data]).encode('utf-8'))

                    run_result = self.sock.get_socket().recv(1024).decode('utf-8').lower()
                    if run_result == 'test finished':
                        log.info('[launch_test]Test {} Finished'.format(data.get('name')))
                    elif run_result.startswith('test failed'):
                        log.error('[launch_test]Test {} Failed because of exception'.format(data.get('name')))
                    else:
                        log.error('xxxxxxx get incorrect feed back during test xxxxxxx')
                else:
                    log.error('xxxxxx get incorrect feed back before test xxxxxxxxxxx')
        except:
            log.error('[launch_test] meet exception: {}'.format(traceback.format_exc()))

    def _run(self):
        run_t = threading.Thread(target=self.launch)
        run_t.setDaemon(True)
        run_t.start()
