# -*- coding: utf-8 -*-
# @time     :   4/20/2021 10:00 AM
# @author   :   balance
# @file     :   main_action.py
import os
import time

from Common import email_tool
from Common.common_function import OS

if OS == 'Windows':
    from Common.registry_operator import RegistryTools
    import winsound
from Common.log import log
from Test_Script import \
    (wlan,
     lan,
     storage,
     performance,
     boot,
     reboot)


class RunTest:
    def __init__(self):
        self.status = {}

    def prepare(self):
        if 'windows' in OS.lower():
            # ---disable UAC windows---
            reg = RegistryTools()
            key = reg.open(r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
            reg.create_value(key=key, value_name='EnableLUA', reg_type=1, content=0)
            reg.close(key)

            # ---Firewall----
            os.system('netsh advfirewall set publicprofile state off')
            os.system('netsh advfirewall set privateprofile state off')

    def run_test(self, data: list):
        """
        :param data: list:
            {'name': 'performance', 'loop': 3, 'os': '', 'platform': 't444', 'tester': 'cheng'}
            {'name': 'wlan', 'loop': 3, 'router': 'router1', 'os': '', 'platform': 't444', 'tester': 'cheng'}
            [{'name': 'bootup', 'loop': 60, 'os': '', 'platform': 't444', 'tester': 'cheng'}]
        :return:
        """
        self.status = {}
        # define status as dict: pass to below instance this status will changed as instance's status
        for item in data:
            print(f'item value:{item}')
            if 'storage' in item.get('name', '').lower():
                log.info('[action][run test]begin to test storage')
                self.status['status'] = 'Testing Storage'
                storage.start(item, status=self.status)
                self.status['status'] = 'Test Storage Finished'
                continue
            elif 'performance' in item.get('name', '').lower():
                log.info('[action][run test]begin to test performance')
                self.status['status'] = 'Testing Performance'
                performance.start(item)
                self.status['status'] = 'Test Performance Finished'
                continue
            elif 'bootup' in item.get('name', '').lower():
                log.info('[action][run test]begin to test bootup')
                self.status['status'] = 'Testing Boot Up'
                boot.start(item)
                self.status['status'] = 'Test Boot UP Finished'
                continue
            elif 'reboot' in item.get('name', '').lower():
                log.info('[action][run test]begin to test reboot')
                self.status['status'] = 'Testing Reboot'
                reboot.start(item)
                self.status['status'] = 'Test Reboot Finished'
                continue
            elif 'wlan' in item.get('name', '').lower():
                log.info('[main action][run test]begin to test wlan {}'.format(item.get('router')))
                self.status['status'] = 'Testing Wlan'
                wlan.start(item)
                self.status['status'] = 'Test Wlan {} Finished'.format(item.get('router', ''))
                continue
            elif 'lan' == item.get('name', '').lower():
                log.info('[action][run test]begin to test lan')
                self.status['status'] = 'Testing Lan'
                lan.start(item)
                self.status['status'] = 'Test Lan Finished'
                continue
            elif 'thin' == item.get('name', '').lower():
                log.info('[action][run test]begin to test thinupdate')
                self.status['status'] = 'Testing thinupdate'
                lan.start(item)
                self.status['status'] = 'Test Lan Finished'
                continue

            else:
                log.error(
                    '[main action][main]Get incorrect test item name: {}, please double check'.format(item.get('name')))
                continue

        if data:
            try:
                receiver = ['sunny.tao@hp.com', 'rengui.li@hp.com']
                for test in data:
                    if test.get('name', '').lower() in ['storage', 'lan', 'wlan', 'performance', 'boot up', 'reboot','thin']:
                        additional_email = test.get('email')
                        additional_tester = test.get('tester')
                        if additional_email:
                            receiver.append(additional_email)
                        if additional_tester:
                            receiver.append(additional_tester)
                receiver = list(set(receiver))  # remove duplicate email

                # wlan should be tested alone, and report zip file will be sent to controller that sends email to tester
                if len(data) == 1 and 'wlan' in data[0].get('name', ''):
                    # send a email to tester after finishing wlan test
                    if int(data[0].get('current_config_count')) == int(data[0].get('total_config_count')):
                        log.info("[RunTest][run_test]start compress report to zip-format file")
                        file = email_tool.zip_dir()
                        log.info("[RunTest][run_test]zip file path:{}".format(file))

                        email_tool.send_mail(recipient=receiver,
                                             subject='Functional Performance Test Report',
                                             attachment=file)
                        os.remove(file)
                    else:
                        log.info(
                            f"[RunTest][run_test]current-config/total-config:"
                            f"{data[0].get('current_config_count')}/{data[0].get('total_config_count')}")

                else:
                    log.info("[RunTest][run_test]start compress report to zip-format file")
                    file = email_tool.zip_dir()
                    log.info("[RunTest][run_test]zip file path:{}".format(file))

                    email_tool.send_mail(recipient=receiver,
                                         subject='Functional Performance Test Report',
                                         attachment=file)
                    os.remove(file)

                if OS == 'Windows':
                    for i in range(3):
                        winsound.Beep(300, 1000)
                        time.sleep(0.5)

            except Exception as e:
                import traceback
                log.error('[RunTest][run_test]meet exception at the end: {}'.format(traceback.format_exc()))


if __name__ == '__main__':
    pass
