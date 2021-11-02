# -*- coding: utf-8 -*-
# Form implementation generated from reading ui file 'main_ui.ui'
# Created by: PyQt5 UI code generator 5.13.0
# WARNING! All changes made in this file will be lost!
import ctypes
import os
import platform
import threading
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

from Common.file_operator import YamlOperator
from Common.log import log
from Common.socket_action import SocketClient
from Common.tc_info import WESInfo, LinuxInfo

if 'window' in platform.platform().lower():
    # set icon for taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


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
                border-radius:1px;
                font-size:12px;
                height:40px;
                padding-left:10px;
                padding-right:10px;
                text-align:center;
                }
            """
    status = """
                QLabel{
                border:none;
                color:black;
                border:1px solid #F3F3F5;
                border-radius:10px;
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


class BaseUI(object):
    status = pyqtSignal()

    def __init__(self, Form):
        self.sock: SocketClient = None
        self.test_item = self.get_config()
        self.run_test = None
        self.setup_ui(Form)

    @staticmethod
    def get_config():
        data = {}

        if os.path.exists(r'./Test_Data/td_common/global_config.yml'):
            source = YamlOperator(r'./Test_Data/td_common/global_config.yml').read()
            data['performance'] = source.get('performance')
            data['storage'] = source.get('storage')
            data['router'] = source.get('router')
            data['port'] = source.get('port')
            data['uut_information'] = source.get('uut_information')
            data['router_support'] = source.get('router_support')
            data['test_data'] = source.get('test_data')
        else:
            data['performance'] = {'wes': 'Passmark', 'linux': 'Geekbench'}
            data['storage'] = {'wes': 'Diskmark', 'linux': 'DD Command'}
            data['router'] = {'router1', 'router2'}
            data['uut_information'] = ['os_version', 'platform', 'memory', 'storage', 'cpu']
            data['test_data'] = {'performance_loop': 3, 'storage_loop': 3,
                                 'wlan_loop': 3, 'lan_loop': 3, 'bootup_loop': 3,
                                 'reboot_loop': 3, 'thin_loop': 3,
                                 'deviation': 0.05}
            data['router_support'] = {'test': 'test'}

        return data

    def setup_ui(self, Form):
        Form.setObjectName("Form")
        Form.resize(460, 627)
        Form.setAutoFillBackground(False)
        Form.setStyleSheet(UIStyleSheet.common)

        self.status_bar = QtWidgets.QLabel(Form)
        self.status_bar.setGeometry(QtCore.QRect(10, 595, 440, 25))
        self.status_bar.setText('wait to test case')
        self.status_bar.setStyleSheet(UIStyleSheet.label)

        self.btn_launch = QtWidgets.QPushButton(Form)
        self.btn_launch.setGeometry(QtCore.QRect(310, 565, 75, 25))
        self.btn_launch.setObjectName("launchButton")
        self.btn_launch.clicked.connect(self._run)

        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setGeometry(QtCore.QRect(20, 70, 420, 490))
        self.tabWidget.setObjectName("tabWidget")

        self.test_ui = QtWidgets.QWidget()
        self.test_ui.setObjectName("Test")

        self.tabWidget.addTab(self.test_ui, "")
        self.frame = QtWidgets.QFrame(self.test_ui)
        self.frame.setGeometry(QtCore.QRect(0, 0, 390, 450))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.os_comb = QtWidgets.QComboBox(self.frame)
        for _os in self.test_item.get('performance').keys():
            self.os_comb.addItem(_os)
        self.os_comb.setGeometry(QtCore.QRect(120, 50, 113, 20))
        self.os_comb.setObjectName("os_comb")
        self.os_comb.currentTextChanged.connect(self.os_depend)

        self.label_os = QtWidgets.QLabel(self.frame)
        self.label_os.setGeometry(QtCore.QRect(20, 50, 71, 21))
        self.label_os.setObjectName("os_label")

        self.platform_label = QtWidgets.QLabel(self.frame)
        self.platform_label.setGeometry(QtCore.QRect(20, 80, 71, 21))
        self.platform_label.setObjectName("platform_label")
        self.platform_edit = QtWidgets.QLineEdit(self.frame)
        self.platform_edit.setGeometry(QtCore.QRect(120, 80, 113, 20))
        self.platform_edit.setObjectName("platform_edit")
        self.platform_edit.setPlaceholderText('Platform')
        self.platform_edit.setObjectName("platform_edit")

        self.tester_edit = QtWidgets.QLineEdit(self.frame)
        self.tester_edit.setGeometry(QtCore.QRect(120, 110, 113, 20))
        self.tester_edit.setObjectName("tester_edit")
        self.tester_edit.setPlaceholderText('example@hp.com')
        self.tester_label = QtWidgets.QLabel(self.frame)
        self.tester_label.setGeometry(QtCore.QRect(20, 110, 71, 21))
        self.tester_label.setObjectName("tester_label")

        self.frame_test = QtWidgets.QFrame(self.frame)
        self.frame_test.setGeometry(QtCore.QRect(0, 150, 371, 301))
        self.frame_test.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_test.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_test.setObjectName("frame_test")

        self.performance_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.performance_chkbox.setGeometry(QtCore.QRect(20, 200, 141, 31))
        self.performance_chkbox.setObjectName("performance_chkbox")
        self.perfomance_comb = QtWidgets.QComboBox(self.frame_test)
        self.perfomance_comb.setGeometry(QtCore.QRect(120, 200, 111, 22))
        self.perfomance_comb.setObjectName("performance_combobox")
        self.perfomance_comb.setDisabled(True)

        for k, v in self.test_item.get('performance').items():
            self.perfomance_comb.addItem(v)
        self.perfomance_comb.setDisabled(True)

        self.storage_chkbox = QtWidgets.QCheckBox(self.frame_test)
        self.storage_chkbox.setGeometry(QtCore.QRect(20, 240, 141, 31))
        self.storage_chkbox.setObjectName("storage_checkbox")
        self.storage_comb = QtWidgets.QComboBox(self.frame_test)
        self.storage_comb.setGeometry(QtCore.QRect(120, 240, 111, 22))
        self.storage_comb.setObjectName("storage_comboBox")
        self.storage_comb.setDisabled(True)

        for k, v in self.test_item.get('storage').items():
            self.storage_comb.addItem(v)
        self.storage_comb.setDisabled(True)

        # add tab router
        self.router = QtWidgets.QWidget()
        self.router.setObjectName("Router")
        self.frame_uut_info = QtWidgets.QFrame(self.router)

        # define global dict to store edit widget for uut information
        self.uut_info_dict = {}
        self.__h = 0  # last edit's hight

        for uut_item in self.test_item.get('uut_information'):
            label = QtWidgets.QLabel(self.router)
            label.setText(uut_item)
            label.setGeometry(QtCore.QRect(10, 20 + self.__h, 250, 20))
            edit = QtWidgets.QLineEdit(self.router)
            self.uut_info_dict[uut_item] = edit
            edit.setGeometry(QtCore.QRect(120, 20 + self.__h, 250, 20))
            self.__h += 30

        # # add save button
        # save_btn = QtWidgets.QPushButton(self.router)
        # save_btn.setText('Save')
        # save_btn.setGeometry(QtCore.QRect(120, 20 + self.__h, 250, 20))
        # save_btn.clicked.connect(self.__save_info)

        self.tabWidget.addTab(self.router, "")

        if 'window' in platform.platform().lower():
            self.os_comb.setCurrentText('wes')
        else:
            self.os_comb.setCurrentText('linux')
        self.os_comb.setDisabled(True)

        self.title_label = QtWidgets.QLabel(Form)
        self.title_label.setStyleSheet(UIStyleSheet.label_title)
        self.title_label.setGeometry(QtCore.QRect(70, 20, 341, 41))

        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)

        self.title_label.setFont(font)
        self.title_label.setObjectName("title_label")

        self.hp_icon_label = QtWidgets.QLabel(Form)
        self.hp_icon_label.setGeometry(QtCore.QRect(0, 0, 461, 631))
        self.hp_icon_label.setText("")
        self.hp_icon_label.setPixmap(QtGui.QPixmap("./Test_Data/main_bg.jpg"))
        self.hp_icon_label.setObjectName("hp_icon_container_label")

        # set top level widget
        self.hp_icon_label.raise_()
        self.status_bar.raise_()
        self.btn_launch.raise_()
        self.tabWidget.raise_()
        self.title_label.raise_()

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Functional Performance"))
        Form.setWindowIcon(QIcon(r'./Test_Data/hp.ico'))

        self.btn_launch.setText(_translate("Form", "Launch"))
        self.label_os.setText(_translate("Form", "OS"))
        self.performance_chkbox.setText(_translate("Form", "Performance"))
        self.storage_chkbox.setText(_translate("Form", "Storage"))
        self.platform_label.setText(_translate("Form", "Platform"))
        self.tester_label.setText(_translate("Form", "Tester"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.test_ui), _translate("Form", "Test"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.router), _translate("Form", "UUTInfo"))
        self.title_label.setText(_translate("Form", "Performance Automation Test"))

    def os_depend(self):
        if self.os_comb.currentText().lower() in list(self.test_item.get('performance').keys()):
            self.perfomance_comb.setCurrentText(
                self.test_item.get('performance').get(self.os_comb.currentText().lower()))
            self.storage_comb.setCurrentText(self.test_item.get('storage').get(self.os_comb.currentText().lower()))

    def fill_local_uut_info(self):
        if self.os_comb.currentText() == 'wes':
            uut = WESInfo()
        else:
            uut = LinuxInfo()

        for i in self.test_item.get('uut_information'):
            try:
                if 'memory' in i.lower():
                    # format memory information, there might be 2 rams
                    rams = eval('uut.{}'.format(i))
                    ram = rams[0].get('output') if len(rams) == 1 else rams[0].get('output') + rams[1].get('output')
                    self.uut_info_dict[i].setText(str(ram))
                elif 'mac_info' in i.lower():
                    if self.os_comb.currentText() == 'wes':
                        self.uut_info_dict[i].setText(str(eval('uut.{}(ip="127.0.0.1").get("output")'.format(i))))
                else:
                    self.uut_info_dict[i].setText(str(eval('uut.{}[0].get("output")'.format(i))))
            except AttributeError:
                log.debug('[main agent][fill local uut]skip {}'.format(i))
            except:
                log.error(traceback.format_exc())

    def launch(self):
        self.btn_launch.setDisabled(True)
        self.btn_launch.setStyleSheet("""
            background-color:LightGreen;
        """)
        # get uut information data
        _os = self.os_comb.currentText()
        _platform = self.platform_edit.text()
        tester = self.tester_edit.text()
        general_data = {'os': _os, 'platform': _platform, 'tester': tester}
        for name in self.test_item.get('uut_information'):
            general_data[name] = self.uut_info_dict[name].text()

        if self.performance_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing performance ...')

            perf_data = {'name': 'performance',
                         'loop': self.test_item.get('test_data').get('performance_loop')}
            # bench = self.perfomance_comb.currentText()

            perf_data.update(general_data)
            self.run_test.run_test([perf_data])
            self.performance_chkbox.setCheckState(QtCore.Qt.Unchecked)

        if self.storage_chkbox.checkState() == QtCore.Qt.Checked:
            self.status_bar.setText('Testing Storage ...')

            storage_data = {'name': 'storage',
                            'loop': self.test_item.get('test_data').get('storage_loop'),
                            'deviation': self.test_item.get('test_data').get('deviation')}

            storage_data.update(general_data)
            self.run_test.run_test([storage_data])
            self.storage_chkbox.setCheckState(QtCore.Qt.Unchecked)

        self.status_bar.setText('All Test Finished')
        self.btn_launch.setEnabled(True)
        self.btn_launch.setStyleSheet("""
            background-color:LightGray;
        """)

    def _run(self):
        run_t = threading.Thread(target=self.launch)
        run_t.setDaemon(True)
        run_t.start()
