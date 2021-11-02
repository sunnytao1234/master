import json
import os
import platform
import shutil
import socket
import subprocess
import threading
import time
import traceback

from Common.log import log
from Test_Script.base.main_action import RunTest

if 'window' in platform.platform().lower():
    from Common.tc_info import WESInfo as uut_info
    import win32security, win32api, win32con, win32ts, win32process
else:
    from Common.tc_info import LinuxInfo as uut_info

encoding = 'utf-8'
BUFFSIZE = 2048


# class __AgentAction(threading.Thread):
#     """Agent logic according client's command"""
#
#     def __init__(self, socket_conn: socket.socket):
#         super().__init__()
#         self.__sock = socket_conn
#
#     def operate(self, request):
#         log.info(f"[AgentAction][operate]current request is:{request}")
#
#         if request.get('name').upper() == 'BYE':
#             log.info("[AgentAction]client request close socket, Connection Closed")
#             self.__sock.close()
#             return False
#         elif request.get('name').upper() == 'START_TEST':
#             try:
#                 # if len(request['data']) == 1 and 'wlan' in request['data']['name']:
#                 #     request['data']=self
#
#                 RunTest().run_test(request.get('data'))
#                 self.__sock.sendall(json.dumps({'name': 'START_TEST',
#                                                 'data': {'status': 'pass',
#                                                          'notes': 'TEST FINISHED'}}).encode(encoding))
#             except:
#                 self.__sock.sendall(json.dumps({'name': 'START_TEST',
#                                                 'data': {'status': 'failed',
#                                                          'notes': 'TEST FAILED_{}'.format(
#                                                              traceback.format_exc())}}).encode(encoding))
#             return True
#         elif request.get('name').upper() == 'HEARTBEAT':
#             self.__sock.sendall(json.dumps({'name': 'heartbeat',
#                                             'data': 'alive'}).encode(encoding))
#             log.debug('[socket agent]socket is alive')
#             return True
#         elif request.get('name').strip().upper() == 'COMMAND':
#             log.info('[Agent Action][run]receive command: {}'.format(request.get('data')))
#             run_result = self.run_scripts(request.get('data'))
#             log.debug(f'[Agent Action][run]Agent execute command result: {run_result}')
#             if run_result is False:
#                 self.__sock.sendall(json.dumps({'name': 'command',
#                                                 'data': {'status': 'Fail',
#                                                          'notes': 'run scripts fail'}}).encode(encoding))
#             elif len(run_result) > 0:
#                 self.__sock.sendall(json.dumps({'name': 'command',
#                                                 'data': {'status': 'pass',
#                                                          'result': str(run_result),
#                                                          'note': 'run scripts pass'}}).encode(encoding))
#             else:
#                 self.__sock.sendall(json.dumps({'name': 'command',
#                                                 'data': {'status': 'pass',
#                                                          'result': 'None',
#                                                          'note': 'run scripts pass'}}).encode(encoding))
#         elif request.get('name').upper() == 'EXECUTE':
#             try:
#                 self.runProcessInteractWithUser(request.get('data'))
#                 self.__sock.sendall(json.dumps({'name': 'execute',
#                                                 'data': {'status': 'pass',
#                                                          'result': 'None',
#                                                          'note': 'run file pass'}}).encode(encoding))
#
#             except:
#                 self.__sock.sendall(json.dumps({'name': 'execute',
#                                                 'data': {'status': 'fail',
#                                                          'result': 'None',
#                                                          'note': 'run file fail: {}'.format(
#                                                              traceback.format_exc())}}).encode(encoding))
#
#         elif request.get('name').strip().upper() == 'DEPLOY':
#             head_info: dict = json.loads(request.get('data'))
#             file_path = head_info.get('remote_path')
#             file_size = head_info.get('file_size')
#             log.info('[Agent Action][run]receive deploy command: {}'.format(file_path))
#             self.__sock.sendall(json.dumps({'name': 'deploy',
#                                             'data': {'status': 'pass',
#                                                      'result': 'None',
#                                                      'note': 'get head info'}}).encode(encoding))
#
#             recv_len = 0
#             if os.path.exists(file_path):
#                 os.remove(file_path)
#             if not os.path.exists(os.path.dirname(file_path)):
#                 os.mkdir(os.path.dirname(file_path))
#             f = open(file_path, 'ab')
#             while recv_len < file_size:
#                 recv_msg = json.loads(self.__sock.recv(BUFFSIZE).decode(encoding))
#                 if recv_msg.get('name').upper() == 'DEPLOY':
#                     msg = recv_msg.get('data').encode(encoding)
#                     f.write(msg)
#                     recv_len += len(msg)
#                 else:
#                     self.operate(recv_msg)
#             f.close()
#             self.__sock.sendall(json.dumps({'name': 'deploy',
#                                             'data': {'status': 'pass',
#                                                      'result': 'None',
#                                                      'note': 'deploy file finished'}}).encode(encoding))
#
#         elif request.get('name').upper() == 'CAPTURE':
#             file_path = request.get('data').get('file_path')
#             log.info('[Agent Action][run]receive capture command: {}'.format(file_path))
#             if not os.path.exists(file_path):
#                 log.info('[Agent Action][run]file or folder {} not exist'.format(file_path))
#                 self.__sock.sendall(json.dumps({'name': 'capture',
#                                                 'data': {'status': 'fail',
#                                                          'result': 'None',
#                                                          'note': 'file or folder: {} not exist'.format(
#                                                              file_path)}}).encode(encoding))
#
#             if os.path.isdir(file_path):
#                 log.debug(f'{file_path} is folder')
#                 self.send_folder(file_path, [])
#
#             else:
#                 log.debug(f'{file_path} is file')
#                 self.send_file(file_path)
#
#         else:
#             log.info('[Agent Action]Invalid message {}.'.format(request))
#             self.__sock.sendall(json.dumps({'name': 'unknown',
#                                             'data': {'status': 'fail',
#                                                      'result': 'None',
#                                                      'note': 'Invalid message from client'}}).encode(encoding))
#
#     def run(self):
#         while True:
#             if not self.__sock:
#                 log.info('[Agent Action]Connection break...')
#                 break
#             try:
#                 data = self.__sock.recv(BUFFSIZE)
#             except ConnectionAbortedError:
#                 log.info('[Agent Action]Client disconnected ')
#                 break
#             if not data:
#                 try:
#                     print('receive none-->{}<--'.format(data))
#                     log.info('[Agent Action]Receive nothing from client.')
#                     self.__sock.sendall(json.dumps({'name': 'staff',
#                                                     'data': {'status': 'fail',
#                                                              'result': 'None',
#                                                              'note': 'Receive empty message from client'}}).encode(
#                         encoding))
#                     continue
#                 except:
#                     self.__sock.close()
#                     break
#
#             string = data.decode(encoding)
#             print(type(string), string)
#             try:
#                 req_from_client = json.loads(string)
#                 print(type(req_from_client), req_from_client)
#                 # request format: {name: 'bye', data: {}}
#                 log.debug("[Agent Action]Content from client: {}.".format(string))
#                 if self.operate(req_from_client) is False:
#                     break
#             except:
#                 print('--------------------------')
#                 print(string)
#                 print('get data not json format', traceback.format_exc())
#                 print('--------------------------')
#                 continue
#
#     @staticmethod
#     def runProcessInteractWithUser(file_name):
#         hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(),
#                                                 win32con.TOKEN_DUPLICATE | win32con.TOKEN_ADJUST_DEFAULT |
#                                                 win32con.TOKEN_QUERY | win32con.TOKEN_ASSIGN_PRIMARY)
#         hNewToken = win32security.DuplicateTokenEx(hToken, win32security.SecurityImpersonation,
#                                                    win32security.TOKEN_ALL_ACCESS, win32security.TokenPrimary)
#         # Create sid level
#         sessionId = win32ts.WTSGetActiveConsoleSessionId()
#         win32security.SetTokenInformation(hNewToken, win32security.TokenSessionId, sessionId)
#         priority = win32con.NORMAL_PRIORITY_CLASS | win32con.CREATE_NEW_CONSOLE
#         startup = win32process.STARTUPINFO()
#         handle = win32process.CreateProcessAsUser(hNewToken, file_name,
#                                                   None, None, None, False, priority, None, None,
#                                                   startup)
#         # handle = (handle, thread_id, pid, tid)
#
#     def send_file(self, file_path):
#         """
#         send file to client
#         :param file_name:
#         :return:
#         """
#         log.debug('bengin to send file {}'.format(file_path))
#         with open(file_path, 'rb') as f:
#             size = len(f.read())
#             dirc = {'name': 'capture',
#                     'data': {'file_path': file_path,
#                              'file_size': size}
#                     }
#         self.__sock.sendall(f'{json.dumps(dirc)}'.encode(encoding))
#
#         with open(file_path, 'rb') as f_local:
#             data = f_local.read()
#             self.__sock.sendall(json.dumps({'name': 'capture',
#                                             'data': data}).encode(encoding))
#
#     def send_folder(self, folder_name, files):
#         """
#         get all file from folder_name, then send file list to client
#         :param folder_name:
#         :param files:
#         :return:
#         """
#         names = os.listdir(folder_name)
#         for name in names:
#             file_name = os.path.join(folder_name, name)
#             if os.path.isdir(file_name):
#                 self.send_folder(file_name, files)
#             else:
#                 files.append(file_name)
#         self.__sock.sendall(json.dumps({'name': 'capture', 'data': files}).encode(encoding))
#
#     @staticmethod
#     def run_scripts(scripts):
#         try:
#             p = subprocess.Popen(scripts, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT,
#                                  shell=True)
#             result = p.stdout.readlines()
#             return result
#         except:
#             log.error('[Agent Action]Run scripts meet exception:\n{}'.format(traceback.format_exc()))
#             return False


# class __SocketClient:
#     """class of socket client"""
#
#     def __init__(self):
#         self.__sock_client = socket.socket()
#         self.client_ip = ''
#         self.client_port = 0
#
#     def get_socket(self):
#         return self.__sock_client
#
#     def set_connection(self, ip, port):
#         self.client_ip = ip
#         self.client_port = port
#
#     def connect(self):
#         """
#         connect to socket server according ip and port
#         :return: None
#         """
#         log.info('[SocketClient][connect]Begin to connect: host: {}-{}'.format(self.client_ip, self.client_port))
#         try:
#             self.__sock_client = socket.socket()
#             self.__sock_client.connect((self.client_ip, self.client_port))
#             log.info('[SocketClient]Successfully connect to host: {}-{}'.format(self.client_ip, self.client_port))
#             return True
#         except:
#             log.debug("[Socket Client]Socket exception, failed to connect to agent")
#             return False
#
#     def operate(self, response):
#         if response.get('name').upper() == 'HEARTBEAT':
#             if response.get('data').upper() == 'ALIVE':
#                 log.debug('heartbeat {}'.format(response))
#                 return True
#             else:
#                 log.debug('[heartbeat] connection disconnected, {}'.format(response))
#                 return False
#
#     def execute(self, file_name):
#         """
#         run program with UI in services mode
#         :param file_name: full path name
#         :return:
#         """
#         command = json.dumps({'name': 'execute', 'data': file_name})
#         try:
#             log.info('[SocketClient][execute]run: {}'.format(command))
#             self.__sock_client.sendall(command.encode(encoding))
#             data = json.loads(self.__sock_client.recv(BUFFSIZE).decode(encoding, 'ignore'))
#             log.debug('[SocketClient][execute]get response from agent: \n{}'.format(data))
#             if data.get('name').upper() == 'EXECUTE':
#                 if data.get('data').get('status').upper() == 'PASS':
#                     return True
#                 else:
#                     return False
#             else:
#                 log.error('[SocketClient][execute]Failed to execute file: {},'.format(file_name))
#                 return False
#         except:
#             log.error('[SocketClient][execute]Failed to Send command: {},'
#                       'Exception:\n{}'.format(command, traceback.format_exc()))
#             return False
#
#     def heartbeat(self):
#         try:
#             self.__sock_client.sendall(json.dumps({'name': 'heartbeat', 'data': 'test'}).encode(encoding))
#             data = json.loads(self.__sock_client.recv(1024).decode(encoding))
#             if data.get('name').upper() == 'HEARTBEAT':
#                 if data.get('data').upper() == 'ALIVE':
#                     log.debug('heartbeat {}'.format(data.get('data')))
#                     return True
#                 else:
#                     log.debug('[heartbeat] connection disconnected, {}'.format(data.get('data')))
#                     return False
#         except:
#             log.error(traceback.format_exc())
#             return False
#
#     def send_command(self, command):
#         """
#         send command to socket server, return command execute result
#         :param command: windows command, linux command
#         :return: command execute result
#         """
#         command_convert = json.dumps({'name': 'command', 'data': command})
#         try:
#             log.info('[Socket Client]Send command: {}'.format(command))
#             self.__sock_client.sendall(command_convert.encode(encoding))
#             data = self.__sock_client.recv(20480).decode(encoding,
#                                                          'ignore')  # sometimes feedback size very large, here receive 20480
#             log.debug(
#                 '[Socket Client][send command]get response from agent: \n{}'.format(data))
#             data = json.loads(data)
#             if data.get('name').upper() == 'COMMAND':
#                 return data
#             else:
#                 return 'None'
#         except:
#             log.error('[Socket Client][send command]Failed to Send command: {},'
#                       'Exception:\n{}'.format(command, traceback.format_exc()))
#             return ''
#
#     def deploy_file(self, local_path, remote_path):
#         """
#         send file to socket server
#         :param local_path: full path of located file
#         :param remote_path: save as full path in agent server
#         :return: feed back from agent server
#         """
#         try:
#             log.info(f'[Socket Client][deploy file] Begin to send file {local_path}')
#             with open(local_path, 'rb') as f:
#                 size = len(f.read())
#                 dirc = {
#                     'local_path': local_path,
#                     'remote_path': remote_path,
#                     'file_size': size
#                 }
#             head_info = json.dumps(dirc)  # convert dict to string
#             self.__sock_client.sendall(f'deploy:{head_info}'.encode(encoding))
#             log.debug('[Socket Client][deploy file]send file head information to agent')
#             if self.__sock_client.recv(BUFFSIZE).decode(encoding) == 'get file info, begin to download':
#                 with open(local_path, 'rb') as f_local:
#                     data = f_local.read()
#                     self.__sock_client.sendall(data)
#                     return self.__sock_client.recv(2048).decode(encoding)
#             else:
#                 log.error('[Socket Client][deploy file] Fail to deploy '
#                           'file because agent does not receive file information')
#                 return "Fail, agent doesn't get file information"
#         except:
#             log.error(f'[Socket Client][deploy file] Fail becuase exception:\n{traceback.format_exc()}')
#             return False
#
#     def deploy_folder(self, local_path, remote_path, skips=None, keeps=None):
#         """
#         deploy folder to UUT using socket
#         expect skips and keeps should at least one is None, cannot both have value
#         :param local_path:
#         :param remote_path:
#         :param skips: is list if not none, store names that do not want to deploy to uut
#         :param keeps: is lit if not none, store names that only want to deploy to uut
#         :return:
#         """
#         log.info('[][]begin to make folder {}'.format(remote_path))
#         self.send_command('mkdir "{}"'.format(remote_path))
#         names = os.listdir(local_path)
#         # deploy item in keep
#         if keeps:
#             for keep in keeps[:]:
#                 if keep not in names:
#                     keeps.remove(keep)
#             names = keeps
#         # remove item skipped
#         if skips:
#             for skip in skips:
#                 if skip in names:
#                     names.remove(skip)
#         for name in names:
#             file_name = os.path.join(local_path, name)
#             if remote_path.startswith('/'):
#                 remote_name = '{}/{}'.format(remote_path, name)
#             else:
#                 remote_name = os.path.join(remote_path, name)
#             if os.path.isdir(file_name):
#                 self.deploy_folder(file_name, remote_name, skips)
#             else:
#                 self.deploy_file(file_name, remote_name)
#
#     def capture_file(self, local_path, remote_path):
#         """
#         get file from agent server
#         :param local_path: save as located full path
#         :param remote_path: Full path of file in agent server
#         :return: get file result
#         """
#         if os.path.exists(local_path):
#             os.remove(local_path)
#         if not os.path.exists(os.path.dirname(local_path)):
#             os.makedirs(os.path.dirname(local_path))
#         try:
#             log.info(f'[Socket Client][capture file] Begin to capture file {remote_path}')
#             self.__sock_client.sendall(f'capture:{remote_path}'.encode(encoding))
#             feedback = self.__sock_client.recv(BUFFSIZE).decode(encoding)
#             if 'file not exist' in feedback:
#                 return 'Fail, remote file not exist'
#             file_info = json.loads(feedback)
#             file_size = file_info.get('file_size', 0)
#             log.debug(f'[Socket Client][capture file]get head info from agent: {file_info}')
#             recv_len = 0
#             f = open(local_path, 'ab')
#             while recv_len < file_size:
#                 recv_msg = self.__sock_client.recv(BUFFSIZE)
#                 f.write(recv_msg)
#                 recv_len += len(recv_msg)
#             f.close()
#             if os.path.exists(local_path):
#                 log.info(f'[Socket Client][capture file]successfully capture file {local_path} from agent')
#                 return 'Pass, capture finished'
#             else:
#                 log.error(f'[Socket Client][capture file]Failed capture file {local_path} from agent')
#                 return 'Fail, local file not exist'
#         except:
#             log.error(f'[Socket Client][capture file] Fail becuase exception:\n{traceback.format_exc()}')
#             return False
#
#     def capture_folder(self, local_path: str, remote_path: str):
#         """
#         capture folder from uut agent
#         here get remote file list, the capture files using capture_file method
#         :param local_path: local folder to store files from agent
#         :param remote_path: remote folder path, must be a folder
#         :return:
#         """
#         if os.path.exists(local_path):
#             shutil.rmtree(local_path)
#         os.mkdir(local_path)
#         try:
#             log.info(f'[Socket Client][capture folder] Begin to capture folder {remote_path}')
#             self.__sock_client.sendall(f'capture:{remote_path}'.encode(encoding))
#             feedback = self.__sock_client.recv(BUFFSIZE).decode(encoding)
#             if 'file not exist' in feedback:
#                 log.error('Folder or file {} not Exist, please check spell of name'.format(remote_path))
#                 return 'Fail, remote file not exist'
#             file_list = json.loads(feedback)
#             for file in file_list:
#                 # convert '\\' to / in folder, because all os should support '/' in path
#                 local_name = file.replace(remote_path, local_path).replace('\\', '/')
#                 self.capture_file(local_name, file)
#         except:
#             log.error(f'[Socket Client][capture file] Fail becuase exception:\n{traceback.format_exc()}')
#             return False
#
#     def close(self):
#         """
#         1. disconnect connection from agent
#         2. close client connection
#         :return: NOne
#         """
#         self.__sock_client.sendall('bye'.encode(encoding))  # agent disconnect
#         self.__sock_client.close()  # client disconnect
#         log.info('[Socket Client]client request disconnect from server')


class _AgentAction(threading.Thread):
    """Agent logic according client's command"""

    def __init__(self, socket_conn: socket.socket):
        super().__init__()
        self.__sock = socket_conn

    def run(self):
        while True:
            if not self.__sock:
                log.info('[Agent Action]Connection break...')
                break

            try:
                data = self.__sock.recv(BUFFSIZE)
            except ConnectionAbortedError:
                log.info('[Agent Action]Client disconnected ')
                break

            if not data:
                try:
                    print('receive none-->{}<--'.format(data))
                    log.info('[Agent Action]Receive nothing from client.')
                    self.__sock.sendall('Fail,Receive nothing from client'.encode(encoding))
                    continue
                except:
                    self.__sock.close()
                    break

            string = data.decode(encoding)
            # request format: {name: 'bye', data: {}}
            log.debug("[Agent Action]Content from client: {}.".format(string))
            string_list = string.split(':', 1)
            if string.upper() == 'BYE':
                log.info("[Agent Action]client request close socket, Connection Closed")
                self.__sock.close()
                break
            elif string.upper() == 'START_TEST':
                self.__sock.sendall('accept test'.encode(encoding))
                test_data = self.__sock.recv(2048).decode(encoding)
                data = json.loads(test_data)
                time.sleep(3)
                try:
                    RunTest().run_test(data)
                except ConnectionResetError:
                    log.warning(
                        f"[AgentAction][run]after running test script, receive a exception:{traceback.format_exc()}")
                    self.__sock.close()
                    break
                try:
                    self.__sock.sendall('TEST FINISHED'.encode(encoding))
                except ConnectionResetError:
                    log.warning(
                        f"[AgentAction][run]after running test script, receive a exception:{traceback.format_exc()}")
                    self.__sock.close()
                    break
                except:
                    self.__sock.sendall('TEST FAILED_{}'.format(traceback.format_exc()).encode(encoding))
                continue
            elif string.upper() == 'UUT_INFO':
                uut = uut_info()
                bios = uut.bios_info
                memory = uut.memory_info
                disk = uut.disk_info
                cpu = uut.cpu_info
                vga = uut.gpu_info
                main_board = uut.main_board_info
                platform_ = uut.platform_info
                ml = uut.ml_info
                os_ = uut.os_info

                if 'windows' in platform.platform().lower():
                    mac = uut.mac_info(ip=self.__sock.getsockname()[0])
                else:
                    mac=uut.mac_info

                uut_info_dict = {'memory_info': memory,
                                 'bios_info': bios,
                                 'disk_info': disk,
                                 'cpu_info': cpu,
                                 'gpu_info': vga,
                                 'main_board_info': main_board,
                                 'platform_info': platform_,
                                 'ml_info': ml,
                                 'os_info': os_,
                                 'mac_info': mac,
                                 }
                self.__sock.sendall(f'{json.dumps(uut_info_dict)}'.encode(encoding))
                log.debug('agent send uut info to client: {}'.format(uut_info_dict))
            elif string.upper() == 'HEARTBEAT':
                self.__sock.sendall('alive'.encode(encoding))
                log.debug('[socket agent]socket is alive')
                continue
            elif string_list[0].strip().upper() == 'CMD':
                script = string_list[1].strip()
                log.info('[Agent Action][run]receive command: {}'.format(script))
                run_result = self.run_scripts(script)
                log.debug(f'[Agent Action][run]Agent execute cmd: {script} result: {run_result}')
                if run_result is False:
                    self.__sock.sendall('Fail,run scripts fail'.encode(encoding))
                elif len(run_result) > 0:
                    result_str = b''.join(run_result)
                    self.__sock.sendall(b'Pass,' + result_str)
                else:
                    self.__sock.sendall('Pass,run scripts done with no return value'.encode(encoding))
                continue
            elif string_list[0].upper() == 'EXEC':
                try:
                    log.debug('get command')
                    self.runProcessInteractWithUser(string_list[1])
                    self.__sock.sendall('pass'.encode(encoding))
                    continue
                except:
                    print(traceback.format_exc())
                    self.__sock.sendall('fail'.encode(encoding))
                    continue
            elif string_list[0].strip().upper() == 'DEPLOY':
                head_info: dict = json.loads(string_list[1])
                file_path = head_info.get('remote_path')
                file_size = head_info.get('file_size')
                log.info('[Agent Action][run]receive deploy command: {}'.format(file_path))
                self.__sock.sendall('get file info, begin to download'.encode(encoding))
                recv_len = 0
                if os.path.exists(file_path):
                    os.remove(file_path)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.mkdir(os.path.dirname(file_path))
                f = open(file_path, 'ab')
                while recv_len < file_size:
                    recv_msg = self.__sock.recv(BUFFSIZE)
                    f.write(recv_msg)
                    recv_len += len(recv_msg)
                f.close()
                self.__sock.sendall('Success'.encode(encoding))
                continue
            elif string_list[0].strip().upper() == 'CAPTURE':
                file_name = string_list[1]
                log.info('[Agent Action][run]receive capture command: {}'.format(file_name))
                if not os.path.exists(file_name):
                    log.info('[Agent Action][run]file or folder {} not exist'.format(file_name))
                    self.__sock.sendall(f'file not exist'.encode(encoding))
                    continue
                if os.path.isdir(file_name):
                    log.debug(f'{file_name} is folder')
                    self.send_folder(file_name, [])
                    continue
                else:
                    log.debug(f'{file_name} is file')
                    self.send_file(file_name)
                continue
            else:
                log.info('[Agent Action]Invalid message {}.'.format(string))
                self.__sock.sendall('Fail,Invalid message from client'.encode(encoding))
                continue

    @staticmethod
    def runProcessInteractWithUser(file_name):
        hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(),
                                                win32con.TOKEN_DUPLICATE | win32con.TOKEN_ADJUST_DEFAULT |
                                                win32con.TOKEN_QUERY | win32con.TOKEN_ASSIGN_PRIMARY)
        hNewToken = win32security.DuplicateTokenEx(hToken, win32security.SecurityImpersonation,
                                                   win32security.TOKEN_ALL_ACCESS, win32security.TokenPrimary)
        # Create sid level
        sessionId = win32ts.WTSGetActiveConsoleSessionId()
        win32security.SetTokenInformation(hNewToken, win32security.TokenSessionId, sessionId)
        priority = win32con.NORMAL_PRIORITY_CLASS | win32con.CREATE_NEW_CONSOLE
        startup = win32process.STARTUPINFO()
        handle = win32process.CreateProcessAsUser(hNewToken, file_name,
                                                  None, None, None, False, priority, None, None,
                                                  startup)
        # handle = (handle, thread_id, pid, tid)

    def send_file(self, file_name):
        """
        send file to client
        :param file_name:
        :return:
        """
        if not os.path.exists(file_name):
            self.__sock.sendall(f'file not exist'.encode(encoding))
            return
        log.debug('bengin to send file {}'.format(file_name))
        with open(file_name, 'rb') as f:
            size = len(f.read())
            dirc = {
                'file_name': file_name,
                'file_size': size
            }
        head_info = json.dumps(dirc)  # convert dict to string
        self.__sock.sendall(f'{head_info}'.encode(encoding))
        with open(file_name, 'rb') as f_local:
            data = f_local.read()
            self.__sock.sendall(data)

    def send_folder(self, folder_name, files):
        """
        get all file from folder_name, then send file list to client
        :param folder_name:
        :param files:
        :return:
        """
        names = os.listdir(folder_name)
        for name in names:
            file_name = os.path.join(folder_name, name)
            if os.path.isdir(file_name):
                self.send_folder(file_name, files)
            else:
                files.append(file_name)
        files = json.dumps(files)
        self.__sock.sendall(f'{files}'.encode(encoding))

    @staticmethod
    def run_scripts(scripts):
        try:
            p = subprocess.Popen(scripts, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                                 shell=True)
            result = p.stdout.readlines()
            return result
        except:
            log.error('[Agent Action]Run scripts meet exception:\n{}'.format(traceback.format_exc()))
            return False


# class ClientAction:
#     def __init__(self, socket_conn):
#         self.__sock = socket_conn


class SocketAgent(threading.Thread):
    """ Socket agent_linux server, all logic depends on AgentAction"""

    def __init__(self, ip: str = "0.0.0.0", port: int = 33333):
        super().__init__()
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(0)

        self.flag = True  # control socket stop

    def run(self):
        log.info("[SocketAgent][run]Socket Agent Listener started")
        while 1:
            try:
                if not self.flag:
                    log.info('[SocketAgent][Run]Socket agent will be closed')
                    break

                client_socket, client_addr = self.sock.accept()
                log.info("[SokcetAgent][Run]Accept a connect from client {}.".format(client_addr))

                agent_action = _AgentAction(client_socket)
                agent_action.setDaemon(True)
                agent_action.start()

                log.info('[SocketAgent][Run]Socket agent is running')
            except OSError:
                log.warning('[SokcetAgent][Run]expected exception because of agent closed')
                break
            except Exception:
                import traceback
                log.error(f"[SokcetAgent][Run]receive a exception:{traceback.format_exc()}")
                break

    def stop(self):
        self.flag = False
        self.sock.close()


class SocketClient:
    """class of socket client"""

    def __init__(self):
        self.__sock_client = socket.socket()
        self.client_ip = ''
        self.client_port = 0

    def get_socket(self):
        return self.__sock_client

    def set_connection(self, ip, port):
        self.client_ip = ip
        self.client_port = port

    def connect(self):
        """
        connect to socket server according ip and port
        :return: None
        """
        log.info('[SocketClient][connect]Begin to connect: host: {}-{}'.format(self.client_ip, self.client_port))
        try:
            self.__sock_client = socket.socket()
            self.__sock_client.connect((self.client_ip, self.client_port))

            log.info('[SocketClient]Successfully connect to host: {}-{}'.format(self.client_ip, self.client_port))
            return True
        except:
            import traceback
            log.debug(f"[Socket Client]Socket exception, failed to connect to agent:{traceback.format_exc()}")
            return False

    def execute(self, file_name):
        """
        run program with UI in services mode
        :param file_name: full path name
        :return:
        """
        command = f'exec:{file_name}'
        try:
            log.info('[SocketClient][execute]run: {}'.format(command))

            self.__sock_client.sendall(command.encode(encoding))
            data = self.__sock_client.recv(BUFFSIZE)
            log.debug('[SocketClient][execute]get response from agent: \n{}'.format(data.decode(encoding, 'ignore')))
            if data == 'pass':
                return True
            else:
                return False
        except:
            log.error('[SocketClient][execute]Failed to Send command: {},'
                      'Exception:\n{}'.format(command, traceback.format_exc()))
            return False

    def heartbeat(self):
        try:
            self.__sock_client.sendall('HEARTBEAT'.encode(encoding))
            data = self.__sock_client.recv(1024).decode(encoding)
            if data.upper() == 'ALIVE':
                log.debug('heartbeat {}'.format(data))
                return True
            else:
                log.debug('[heartbeat] connection disconnected, {}'.format(data))
                return False
        except:
            log.error(traceback.format_exc())
            return False

    def send_command(self, command):
        """
        send command to socket server, return command execute result
        :param command: windows command, linux command
        :return: command execute result
        """
        command = f'cmd:{command}'
        try:
            log.info('[Socket Client]Send command: {}'.format(command))
            self.__sock_client.sendall(command.encode(encoding))
            data = self.__sock_client.recv(20480)  # sometimes feedback size very large, here receive 20480
            log.debug(
                '[Socket Client][send command]get response from agent: \n{}'.format(data.decode(encoding, 'ignore')))
            return data.decode(encoding, errors='ignore')
        except:
            log.error('[Socket Client][send command]Failed to Send command: {},'
                      'Exception:\n{}'.format(command, traceback.format_exc()))
            return ''

    def deploy_file(self, local_path, remote_path):
        """
        send file to socket server
        :param local_path: full path of located file
        :param remote_path: save as full path in agent server
        :return: feed back from agent server
        """
        try:
            log.info(f'[Socket Client][deploy file] Begin to send file {local_path}')
            with open(local_path, 'rb') as f:
                size = len(f.read())
                dirc = {
                    'local_path': local_path,
                    'remote_path': remote_path,
                    'file_size': size
                }
            head_info = json.dumps(dirc)  # convert dict to string
            self.__sock_client.sendall(f'deploy:{head_info}'.encode(encoding))
            log.debug('[Socket Client][deploy file]send file head information to agent')
            if self.__sock_client.recv(BUFFSIZE).decode(encoding) == 'get file info, begin to download':
                with open(local_path, 'rb') as f_local:
                    data = f_local.read()
                    self.__sock_client.sendall(data)
                    return self.__sock_client.recv(2048).decode(encoding)
            else:
                log.error('[Socket Client][deploy file] Fail to deploy '
                          'file because agent does not receive file information')
                return "Fail, agent doesn't get file information"
        except:
            log.error(f'[Socket Client][deploy file] Fail becuase exception:\n{traceback.format_exc()}')
            return False

    def deploy_folder(self, local_path, remote_path, skips=None, keeps=None):
        """
        deploy folder to UUT using socket
        expect skips and keeps should at least one is None, cannot both have value
        :param local_path:
        :param remote_path:
        :param skips: is list if not none, store names that do not want to deploy to uut
        :param keeps: is lit if not none, store names that only want to deploy to uut
        :return:
        """
        log.info('[][]begin to make folder {}'.format(remote_path))
        self.send_command('mkdir "{}"'.format(remote_path))
        names = os.listdir(local_path)
        # deploy item in keep
        if keeps:
            for keep in keeps[:]:
                if keep not in names:
                    keeps.remove(keep)
            names = keeps
        # remove item skipped
        if skips:
            for skip in skips:
                if skip in names:
                    names.remove(skip)
        for name in names:
            file_name = os.path.join(local_path, name)
            if remote_path.startswith('/'):
                remote_name = '{}/{}'.format(remote_path, name)
            else:
                remote_name = os.path.join(remote_path, name)
            if os.path.isdir(file_name):
                self.deploy_folder(file_name, remote_name, skips)
            else:
                self.deploy_file(file_name, remote_name)

    def capture_file(self, local_path, remote_path):
        """
        get file from agent server
        :param local_path: save as located full path
        :param remote_path: Full path of file in agent server
        :return: get file result
        """
        if os.path.exists(local_path):
            os.remove(local_path)
        if not os.path.exists(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))
        try:
            log.info(f'[Socket Client][capture file] Begin to capture file {remote_path}')
            self.__sock_client.sendall(f'capture:{remote_path}'.encode(encoding))
            feedback = self.__sock_client.recv(BUFFSIZE).decode(encoding)
            if 'file not exist' in feedback:
                return 'Fail, remote file not exist'
            file_info = json.loads(feedback)
            file_size = file_info.get('file_size', 0)
            log.debug(f'[Socket Client][capture file]get head info from agent: {file_info}')
            recv_len = 0
            f = open(local_path, 'ab')
            while recv_len < file_size:
                recv_msg = self.__sock_client.recv(BUFFSIZE)
                f.write(recv_msg)
                recv_len += len(recv_msg)
            f.close()
            if os.path.exists(local_path):
                log.info(f'[Socket Client][capture file]successfully capture file {local_path} from agent')
                return 'Pass, capture finished'
            else:
                log.error(f'[Socket Client][capture file]Failed capture file {local_path} from agent')
                return 'Fail, local file not exist'
        except:
            log.error(f'[Socket Client][capture file] Fail becuase exception:\n{traceback.format_exc()}')
            return False

    def capture_folder(self, local_path: str, remote_path: str):
        """
        capture folder from uut agent
        here get remote file list, the capture files using capture_file method
        :param local_path: local folder to store files from agent
        :param remote_path: remote folder path, must be a folder
        :return:
        """
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
        os.mkdir(local_path)
        try:
            log.info(f'[Socket Client][capture folder] Begin to capture folder {remote_path}')
            self.__sock_client.sendall(f'capture:{remote_path}'.encode(encoding))
            feedback = self.__sock_client.recv(BUFFSIZE).decode(encoding)
            if 'file not exist' in feedback:
                log.error('Folder or file {} not Exist, please check spell of name'.format(remote_path))
                return 'Fail, remote file not exist'
            file_list = json.loads(feedback)
            for file in file_list:
                # convert '\\' to / in folder, because all os should support '/' in path
                local_name = file.replace(remote_path, local_path).replace('\\', '/')
                self.capture_file(local_name, file)
        except:
            log.error(f'[Socket Client][capture file] Fail becuase exception:\n{traceback.format_exc()}')
            return False

    def close(self):
        """
        1. disconnect connection from agent
        2. close client connection
        :return: NOne
        """
        self.__sock_client.sendall('bye'.encode(encoding))  # agent disconnect
        self.__sock_client.close()  # client disconnect
        log.info('[Socket Client]client request disconnect from server')
