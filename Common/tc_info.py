# -*- coding: utf-8 -*-
# @time     :   5/28/2021 8:54 AM
# @author   :   balance
# @file     :   tc_info.py
import platform
import re
import subprocess

from Common.common_function import OSTool

if 'windows' in platform.platform().lower():
    import pythoncom

    pythoncom.CoInitialize()
    import wmi

    from Common.registry_operator import RegistryTools


class LinuxInfo:
    cmd = 'dmidecode -t {}'
    """
    bios | system | baseboard | chassis | processor | memory | connector | slot
    """

    @property
    def cpu_info(self):
        p = subprocess.Popen(self.cmd.format('processor'), stdout=subprocess.PIPE, shell=True)
        cpu_data = p.stdout.read().decode('utf-8')

        output = re.findall(r'(?i)Version:\s+(.*?)\n', cpu_data, re.S)[0]
        cpu_cores = re.findall(r'(?i)Core count:\s+(.*?)\n', cpu_data, re.S)[0]

        output = output.replace('@', '{}C@'.format(cpu_cores))

        return [{'CpuCores': cpu_cores, 'output': output}]

    @property
    def memory_info(self):
        info = ''
        try:
            p = subprocess.Popen(self.cmd.format('memory'), stdout=subprocess.PIPE, shell=True)
            result = p.stdout.read().decode('utf-8')

            size = re.findall(r'(?i)Size:\s+(\d{4,5} MB)\n', result, re.S)
            mem_num = re.findall(r'(?i)Configured Clock Speed:\s+\d{4,5}', result, re.S)
            speed_value = subprocess.getoutput("dmidecode -t memory | grep -E \"^\sSpeed\"")
            speed_value = speed_value.split("\n")
            speed = int(speed_value[0].split(' ')[1])
            mem_type = re.findall(r'(?i)Type: DDR\d{0,1}', result, re.S)

            if len(mem_num) > 1:
                info = f'{int(int(size[0].split()[0]) * 2 / 1024)}GB ({int(int(size[0].split()[0]) / 1024)}GB {mem_type[0].split(":")[-1].strip()} {speed}) x {len(speed_value)}'
            else:
                info = f'{int(int(size[0].split()[0]) / 1024)}GB {mem_type[0].split(":")[-1].strip()} {speed}'
        except:
            info = ''

        return [{'output': info}]

    @property
    def mac_info(self):
        result = subprocess.getoutput('ifconfig eth0|grep ether')
        mac_info = result.split()[1].strip().upper()
        return [{'output': mac_info}]

    @property
    def platform_info(self):
        # p = subprocess.Popen(self.cmd.format('system'), stdout=subprocess.PIPE, shell=True)
        # platform_data = p.stdout.read().decode('utf-8')
        # plat_name = re.findall(r'(?i)product name:\s+(.*?)\n', platform_data, re.S)[0]

        value = OSTool.get_platform()

        return [{'output': value}]

    @property
    def ml_info(self):
        info = ''

        image_id = subprocess.getoutput("cat /etc/imageid")
        sp = subprocess.getoutput("dpkg --list | grep hptc-sp-thinpro.*-sp")
        sp = sp.split()[2].strip()

        info = f'{image_id}+SP{sp}'
        # p = subprocess.Popen('dmidecode', stdout=subprocess.PIPE, shell=True)
        # ml_data = p.stdout.read().decode('utf-8')
        # ml_value = re.findall(r'(?i)buildid#(.*?);', ml_data, re.S)
        # if len(ml_value) > 0:
        #     ml = ml_value[0].split('#')[0]
        # else:
        #     ml = ''

        return [{'output': info}]

    @property
    def main_board_info(self) -> list:
        p = subprocess.Popen(self.cmd.format('baseboard'), stdout=subprocess.PIPE, shell=True)
        board_data = p.stdout.read().decode('utf-8')
        output = re.findall(r'(?i)product name:\s+(.*?)\n', board_data, re.S)[0]
        manufacturer = re.findall(r'(?i)manufacturer:\s+(.*?)\n', board_data, re.S)[0]
        return [{'Manufacturer': manufacturer, 'output': output, 'Product': output}]

    @property
    def bios_info(self):
        p = subprocess.Popen(self.cmd.format('bios'), stdout=subprocess.PIPE, shell=True)
        bios_data = p.stdout.read().decode('utf-8')
        output = re.findall(r'(?i)version:\s+(.*?)\n', bios_data, re.S)[0]
        vendor = re.findall(r'(?i)vendor:\s+(.*?)\n', bios_data, re.S)[0]
        release_date = re.findall(r'(?i)release data:\s+(.*?)\n', bios_data, re.S)
        return [{'Manufacturer': vendor, 'ReleaseDate': release_date, 'version': output, 'output': output}]

    @property
    def os_info(self):
        p = subprocess.Popen('cat /etc/issue', stdout=subprocess.PIPE, shell=True)
        os_version = p.stdout.read().decode('utf-8')[:-6].strip()
        p_sp = subprocess.getoutput('dpkg -l | grep hptc-sp.*sp')
        sp_version_value = re.findall('(?i) (\d+.\d+) ', p_sp, re.S)
        if len(sp_version_value) > 0:
            sp_version = sp_version_value[0]
        else:
            sp_version = 'Null'
        return [{'Version': os_version, 'SP': sp_version, 'output': f'{os_version.replace(" ", "")[:-2]}'}]

    @property
    def gpu_info(self):
        # result=subprocess.getoutput('lspci | grep VGA')
        result = ''
        return [{'output': result}]

    @property
    def disk_info(self):
        output = ''
        disk_info = subprocess.getoutput('lsscsi --size')
        if disk_info.strip() != '':
            size = disk_info.split()[-1]

            disk_info = subprocess.getoutput('lsscsi')
            info = disk_info.split('  ')

            output = info[-2] + ' ' + size

        return [{'output': output}]


class WESInfo:
    def __init__(self):
        pythoncom.CoInitialize()
        self.c = wmi.WMI()
        self.reg = RegistryTools()

    def __del__(self):
        pythoncom.CoUninitialize()

    @property
    def ml_info(self):
        try:
            key = self.reg.open(r'SYSTEM\CurrentControlSet\Control\WindowsEmbedded\RunTimeID')
            value = self.reg.get_value(key, 'RunTimeOEMRev')[0]
            return [{'output': value.split('#')[0]}]
        except:
            return [{'output': 'None'}]

    def mac_info(self, ip: str = '127.0.0.1'):
        result = subprocess.getoutput('ipconfig /all')
        result = result.split('\n\n')

        mac = ''
        for res in result:
            if ip in res:
                for mac_line in res.split('\n'):
                    if 'Physical Address' in mac_line:
                        mac = mac_line.split(':')[-1]
                        mac = mac.replace('-', ':').lower().strip()

        return [{'output': mac.upper()}]

    @property
    def platform_info(self):
        # key = self.reg.open(r'HARDWARE\DESCRIPTION\System\BIOS')
        # value = self.reg.get_value(key, 'SystemProductName')[0]

        value = OSTool.get_platform()
        value = value.split()[1]

        return [{'output': value}]

    @property
    def cpu_info(self) -> list:
        tmp_dict = {'CpuCores': 0}

        speed = subprocess.getoutput("wmic cpu get CurrentClockSpeed /value")
        speed = int(speed.replace('\n', '').split('=')[-1])

        for cpu in self.c.Win32_Processor():
            tmp_dict["CpuType"] = cpu.Name
            try:
                tmp_dict["CpuCores"] = cpu.NumberOfCores
            except:
                tmp_dict["CpuCores"] += 1

            tmp_dict['output'] = cpu.Name.replace('@', ' {}C @'.format(cpu.NumberOfCores)) if '@' in cpu.Name \
                else cpu.Name.strip() + ' {}C @ {}MHz'.format(cpu.NumberOfCores, speed)

        return [tmp_dict]

    @property
    def main_board_info(self) -> list:
        board = []
        for b in self.c.Win32_BaseBoard():
            tmp_dict = {'SerialNumber': b.SerialNumber,
                        'Manufacturer': b.Manufacturer,
                        'Product': b.Product,
                        'output': b.Product}
            board.append(tmp_dict)
        return board

    @property
    def bios_info(self) -> list:
        bios = []
        for b in self.c.Win32_BIOS():
            tmp_dict = {'Manufacturer': b.Manufacturer.strip(),
                        'ReleaseDate': b.ReleaseDate,
                        'version': b.SMBIOSBIOSVersion,
                        'output': b.SMBIOSBIOSVersion}
            bios.append(tmp_dict)
        return bios

    @property
    def disk_info(self) -> list:
        """
        :return: all disk information in list
        """
        disk = []
        for d in self.c.Win32_DiskDrive():
            # print disk.__dict__
            tmp_dict = {'SerialNumber': d.SerialNumber.strip(),
                        'DeviceID': d.DeviceID,
                        'Caption': d.Caption,
                        'Size': self.__convert_disk_size(int(int(d.Size) / 1024 ** 3)),
                        'output': '{} {}G'.format(d.Caption,
                                                  self.__convert_disk_size(int(int(d.Size) / 1024 ** 3)))}
            disk.append(tmp_dict)

        return disk

    # @property
    # def memory_info_(self) -> list:
    #     """
    #     get memory information
    #     :return:
    #     """
    #     memory = []
    #     print('get here ----------')
    #     for mem in self.c.Win32_PhysicalMemory():
    #         tmp_dict = {'ConfiguredClockSpeed': mem.ConfiguredClockSpeed,
    #                     'Size': int(int(mem.Capacity) / 1024 ** 3),
    #                     'ConfiguredVoltage': mem.ConfiguredVoltage,
    #                     'Vendor': mem.Manufacturer,
    #                     'output': '{} {}G'.format(mem.Manufacturer, int(int(mem.Capacity) / 1024 ** 3))}
    #         memory.append(tmp_dict)
    #     return memory

    @property
    def memory_info(self):
        memory = []
        info = ''

        for mem in self.c.query('select * from Win32_PhysicalMemory'):
            tmp_dict = {'ConfiguredClockSpeed': mem.ConfiguredClockSpeed,
                        'Size': int(int(mem.Capacity) / 1024 ** 3),
                        'DDR': None,
                        'Speed': mem.Speed,
                        # 'ConfiguredVoltage': mem.ConfiguredVoltage,
                        # 'Vendor': mem.Manufacturer,
                        # 'output': '{} {}G'.format(mem.Manufacturer, int(int(mem.Capacity) / 1024 ** 3))
                        }
            if mem.Speed <= 800:
                if mem.Speed <= 266:
                    tmp_dict['DDR'] = 'DDR'
                else:
                    tmp_dict['DDR'] = 'DDR2'
            elif mem.Speed <= 3200:
                if mem.Speed <= 1600:
                    tmp_dict['DDR'] = 'DDR3'
                else:
                    tmp_dict['DDR'] = 'DDR4'

            memory.append(tmp_dict)

        if len(memory) == 1:
            info = f"{memory[0]['Size']}GB {memory[0]['DDR']} {memory[0]['Speed']}"
        else:
            capability = 0
            for mem in memory:
                capability += mem['Size']

            info = f"{capability}GB ({memory[0]['Size']}GB {memory[0]['DDR']}" \
                   f" {memory[0]['Speed']} x {len(memory)})"

        return [{'output': info}]

    @property
    def gpu_info(self) -> list:
        v_card = []
        for n in self.c.Win32_VideoController():
            if 'Citrix' in n.Description:
                continue

            tmp_dict = {'description': n.Description,
                        'Name': n.Name,
                        'V_processor': n.VideoProcessor,
                        'output': n.Name}
            v_card.append(tmp_dict)

        if len(v_card) >= 2:
            for index, item in enumerate(v_card):
                if 'UHD Graphics' in item['description']:
                    v_card.pop(index)

        return v_card

    @property
    def os_info(self) -> list:
        results = subprocess.getoutput('systeminfo.exe')
        result, *_ = [result.split()[-1] for result in results.split('\n') if 'OS Name:' in result]

        if result.upper() == 'LTSC':
            os_type = 'Win10IOT RS5'
        elif result.upper() == 'LTSB':
            os_type = 'Win10IOT RS1'
        else:
            os_type = 'INCORRECT OS TYPE'

        return [{'output': os_type}]

    @staticmethod
    def __convert_disk_size(size):
        expect_size = [4, 8, 16, 32, 64, 128, 256, 512, 1024, size]
        expect_size.sort()
        return expect_size[expect_size.index(size) + 1]
