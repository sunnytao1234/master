# -*- coding: utf-8 -*-
# @time     :   5/5/2021 3:37 PM
# @author   :   balance
# @file     :   agent.py
from Common.socket_action import SocketAgent
from Test_Script.base.socket_action import SocketAgent as SAgent

# socket agent port 33333
agent = SocketAgent()
agent.start()

wlan_agent = SAgent(listen_ip='0.0.0.0', listen_port=2333)
wlan_agent.open_server()
