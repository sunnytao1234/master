# todo:develop and debug
from Test_Script.base.socket_action import SocketAgent

# use to set environment and test case
server = SocketAgent(server_name='boot_socket_server', listen_ip='0.0.0.0', listen_port=2333)
server.open_server()

# use to recover environment
server = SocketAgent(server_name='boot_socket_server', listen_ip='0.0.0.0', listen_port=2334)
server.open_server()

