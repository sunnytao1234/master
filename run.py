# -*- coding: utf-8 -*-
# @time     :   4/1/2021 3:29 PM
# @author   :   balance
# @file     :   run.py.py

import ctypes
import os
import platform
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

if 'windows' in platform.platform().lower():
    from Test_Script import main_ui
    from Common import common

from Common.socket_action import SocketAgent, SocketClient
from Common import common
from Test_Script.base import main_agent
from Test_Script.base.main_action import RunTest
from Test_Script.base.socket_action import SocketAgent as SAgent
from Test_Script.base.common import check_integrity, recover_ini_env

msg = """\
Test performance for functional automation.
Please Run With Administrator
RUN [option]
    default Launch script with UI for remote test
    /local: Launch script with UI for local test
    /agent: Launch script only for agent in UUT
        """

if __name__ == '__main__':
    if not check_integrity():
        print("The file is missing, please ensure the integrity of the contents")
    else:
        recover_ini_env()

        if len(sys.argv) == 2 and sys.argv[1].lower() in ['/?', '/h', '--help']:
            with open('readme.txt', 'w') as f:
                f.write(msg)
            os.system('notepad readme.txt')
            sys.exit()
        if common.is_admin():
            run_test = RunTest()
            if len(sys.argv) == 1:
                # socket agent port 33333
                if 'windows' in platform.platform().lower():
                    value = common.edit_Screen_baterry_wes()
                else:
                    value = common.edit_Screen_baterry()

                server = SocketAgent(port=33333)
                server.start()

                agent = SAgent(listen_ip='0.0.0.0', listen_port=2333)
                agent.open_server()
            else:
                if len(sys.argv) == 2 and sys.argv[1] == '/local':
                    # shutdown battery save mode
                    if 'windows' in platform.platform().lower():
                        value = common.edit_Screen_baterry_wes()
                    else:
                        value = common.edit_Screen_baterry()

                    run_test.prepare()
                    app = QApplication(sys.argv)
                    wnd = QMainWindow()
                    ui = main_agent.BaseUI(wnd)
                    ui.fill_local_uut_info()
                    ui.run_test = run_test
                    ui.sock = SocketClient()
                    # ui.setup_ui(wnd)
                    wnd.show()
                    sys.exit(app.exec_())

                elif len(sys.argv) == 2 and sys.argv[1] == '/agent':
                    # socket agent port 33333
                    if 'windows' in platform.platform().lower():
                        value = common.edit_Screen_baterry_wes()
                    else:
                        value = common.edit_Screen_baterry()

                    server = SocketAgent(port=33333)
                    server.start()

                    agent = SAgent(listen_ip='0.0.0.0', listen_port=2333)
                    agent.open_server()

                else:
                    # shutdown battery save mode
                    if 'windows' in platform.platform().lower():
                        value = common.edit_Screen_baterry_wes()
                    else:
                        value = common.edit_Screen_baterry()
                    # socket server port 44444
                    server = SocketAgent(port=44444)
                    server.start()
                    app = QApplication(sys.argv)
                    wnd = QMainWindow()
                    ui = main_ui.UIMain(wnd)
                    ui.run_test = run_test
                    ui.sock = SocketClient()
                    # ui.setup_ui(wnd)
                    wnd.show()
                    sys.exit(app.exec_())
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
