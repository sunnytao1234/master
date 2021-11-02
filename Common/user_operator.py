# -*- coding: utf-8 -*-
# @time     :   3/24/2021 4:14 PM
# @author   :   balance
# @file     :   user_operator.py
import traceback

import win32net
import win32netcon

from Common.log import log


class UserGroup:
    def __init__(self):
        self.user_info = dict(
            name='test',
            password='123456',
            priv=win32netcon.USER_PRIV_USER,
            home_dir=None,
            comment=None,
            flags=win32netcon.UF_SCRIPT | win32netcon.UF_DONT_EXPIRE_PASSWD | win32netcon.UF_NORMAL_ACCOUNT,
            script_path=None
        )
        self.group_info = dict(
            domainandname='user'
        )

    @staticmethod
    def check_user(name):
        users, nusers, _ = win32net.NetUserEnum(None, 2)
        for user in users:
            if user.get('name').lower() == name.lower():
                return True
        return False

    @staticmethod
    def del_user(user):
        try:
            win32net.NetUserDel(None, user)
        except:
            pass

    def add_user(self, name, password):
        if self.check_user(name):
            self.del_user(name)
        self.user_info['name'] = name
        self.user_info['password'] = password
        try:
            win32net.NetUserAdd(None, 1, self.user_info)
        except:
            log.error('Add new user [{}] fail'.format(self.user_info['name']))
            log.debug(traceback.format_exc())

    @staticmethod
    def change_passwd(user, old_passwd, new_passwd):
        win32net.NetUserChangePassword(None, user, old_passwd, new_passwd)

    def add_user_to_group(self, user, group='Administrators'):
        # group: Administrators | Users
        self.group_info['domainandname'] = user
        try:
            win32net.NetLocalGroupAddMembers(None, group, 3, [self.group_info])
        except:
            log.error('[user group]fail to add user to group:{}'.format(group))
            log.debug('[user group]{}'.format(traceback.format_exc()))
