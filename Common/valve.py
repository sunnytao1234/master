import time

from serial import Serial

from Common.log import log

# from my_log import get_FileLogger
# log=get_FileLogger()

"""
install com driver
pip uninstall serial
pip uninstall pyserial
pip install pyserial
from serial import Serial
"""


class VALVE:
    """
    default status is open
    """

    def __init__(self, port, bps=9600, timeout=5):
        self.port = port
        self.bps = bps
        self.timeout = timeout
        self._open()

    def _open(self):
        try:
            self.serial = Serial(self.port, self.bps, timeout=self.timeout)
        except Exception as e:
            log.error(e)

    def _send(self, data):
        try:
            result = self.serial.write(data)
            return result
        except Exception as e:
            log.error(e)

    def __del__(self):

        self.serial.close()

    def open(self):
        open_usb_command = b'\xa0\x01\x00\xa1'
        r = self._send(open_usb_command)
        log.info("open USB,res:{}".format(r))
        return r

    def close(self):
        close_usb_command = b'\xa0\x01\x01\xa2'
        r = self._send(close_usb_command)
        log.info("close USB,res:{}".format(r))
        return r


class ValveContainer:

    def __init__(self, port=""):
        self.__port = port

    def set_port(self, port):
        self.__port = port

    def __create_valve(self):
        new_valve = VALVE(self.__port)
        return new_valve

    def open(self):
        """
        create a Valve each time
        """
        new_valve = self.__create_valve()
        new_valve.open()
        del new_valve
        log.info("Open USB serial")

    def close(self):
        """
        close and delete
        """
        new_valve = self.__create_valve()
        new_valve.close()
        del new_valve
        log.info("close USB serial")


if __name__ == '__main__':
    valve = ValveContainer("COM5")
    for _ in range(2):
        valve.close()
        time.sleep(2)
        valve.open()

    # for i in range(3):
    #     log.info("current loop:{}".format(i))
    #     valve.close()
    #     time.sleep(5)
    #     if os.path.exists("d:"):
    #         log.info("disable USB fail")
    #     else:
    #         log.info("disable USB success")
    #
    #     valve.open()
    #     time.sleep(5)
    #     if os.path.exists("d:"):
    #         log.info("enable USB success")
    #     else:
    #         log.info("enable USB fail")
