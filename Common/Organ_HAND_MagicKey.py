import ctypes
import time

from Common.common_function import get_current_dir
from Common.exception import MagicKeyFunctionError
from Common.file_operator import YamlOperator
from Common.log import log


class Magic:
    """
    if you want to use mui, please use function mui_vk_prepare(path)
    HAND_MagicKey : device manager  -> human interface devices -> usb input device -> hardware ids -> vid,pid
    """

    def __init__(self, vp):
        log.info(f'[Magic][init] vp value:{vp}')
        self.log = log
        self.vid = vp[0]
        self.pid = vp[1]
        self.api = ctypes.windll.LoadLibrary(get_current_dir("Test_Utility", "msdk.dll"))
        self.key_handle = self.api.M_Open_VidPid(self.vid, self.pid)
        self.vk_dict_path = get_current_dir(r"Test_Data\magickey_config\MagicKey_KV.yml")
        self.vk_dict = YamlOperator(self.vk_dict_path).read()
        self.res_dic = {}
        self.special_dict = {'!': 'Shift+1', '@': 'Shift+2', '#': 'Shift+3', '$': 'Shift+4', '%': 'Shift+5',
                             '^': 'Shift+6', '&': 'Shift+7', '*': 'Shift+8', '(': 'Shift+9', ')': 'Shift+0',
                             '_': 'Shift+-', '+': 'Shift+=', '{': 'Shift+[', '}': 'Shift+]', '|': 'Shift+\\',
                             'A': 'Shift+a', 'B': "Shift+b", 'C': 'Shift+c', 'D': 'Shift+d', 'E': 'Shift+e',
                             'F': 'Shift+f', 'G': "Shift+g", 'H': 'Shift+h', 'I': 'Shift+i', 'J': 'Shift+j',
                             'K': 'Shift+k', 'L': "Shift+l", 'M': 'Shift+m', 'N': 'Shift+n', 'O': 'Shift+o',
                             'P': 'Shift+p', 'Q': "Shift+q", 'R': 'Shift+r', 'S': 'Shift+s', 'T': 'Shift+t',
                             'U': 'Shift+u', 'V': "Shift+v", 'W': 'Shift+w', 'X': 'Shift+x', 'Y': 'Shift+y',
                             'Z': 'Shift+z', ':': 'Shift+;', '"': "Shift+'", '<': 'Shift+,', '>': 'Shift+.',
                             '?': 'Shift+/'}
        self.special_dict_revert = {'Shift+1': '!', 'Shift+2': '@', 'Shift+3': '#', 'Shift+4': '$', 'Shift+5': '%',
                                    'Shift+6': '^', 'Shift+7': '&', 'Shift+8': '*', 'Shift+9': '(', 'Shift+0': ')',
                                    'Shift+-': '_', 'Shift+=': '+', 'Shift+[': '{', 'Shift+]': '}', 'Shift+\\': '|',
                                    'Shift+;': ':', "Shift+'": '"', 'Shift+,': '<', 'Shift+.': '>', 'Shift+/': '?',
                                    'Shift+a': "A", "Shift+b": "B", "Shift+c": "C", "Shift+d": "D", "Shift+e": "E",
                                    "Shift+f": "F", "Shift+g": "G", "Shift+h": "H", "Shift+i": "I", "Shift+j": "J",
                                    "Shift+k": "K", "Shift+l": "L", "Shift+m": "M", "Shift+n": "N", "Shift+o": "O",
                                    "Shift+p": "P", "Shift+q": "Q", "Shift+r": "R", "Shift+s": "S", "Shift+t": "T",
                                    "Shift+u": "U", "Shift+v": "V", "Shift+w": "W", "Shift+x": "X", "Shift+y": "Y",
                                    "Shift+z": "Z", "Shift+`": "~"}

    @staticmethod
    def _GetScanCodeFromVirtualCode(vcode):
        keymap = {
            "65": 4, "66": 5, "67": 6, "68": 7, "69": 8, "70": 9, "71": 10, "72": 11, "73": 12, "74": 13, "75": 14,
            "76": 15, "77": 16, "78": 17, "79": 18,
            "80": 19, "81": 20, "82": 21, "83": 22, "84": 23, "85": 24, "86": 25, "87": 26, "88": 27, "89": 28,
            "90": 29, "49": 30, "50": 31, "51": 32, "52": 33,
            "53": 34, "54": 35, "55": 36, "56": 37, "57": 38, "48": 39, "13": 40, "27": 41, "8": 42, "9": 43, "32": 44,
            "189": 45, "187": 46, "219": 47, "221": 48,
            "220": 49, "186": 51, "222": 52, "192": 53, "188": 54, "190": 55, "191": 56, "20": 57, "112": 58, "113": 59,
            "114": 60, "115": 61, "116": 62, "117": 63,
            "118": 64, "119": 65, "120": 66, "121": 67, "122": 68, "123": 69, "44": 70, "145": 71, "19": 72,
            "45": 73, "36": 74, "33": 75, "46": 76, "35": 77,
            "34": 78, "39": 79, "37": 80, "40": 81, "38": 82, "144": 83, "111": 84, "109": 86, "107": 87,
            "108": 88, "97": 89, "98": 90, "99": 91, "100": 92,
            "101": 93, "102": 94, "103": 95, "104": 96, "105": 97, "96": 98, "110": 99, "93": 101, "146": 103,
            "173": 127, "175": 128, "174": 129, "162": 224, "160": 225,
            "164": 226, "91": 227, "163": 228, "161": 229, "165": 230, "92": 231, "17": 224, "16": 225, "18": 226,
            "12": 83,
            "42": 70
        }
        vcode = str(vcode)
        if vcode in keymap:
            return keymap[vcode]
        else:
            raise Exception("Not found vcode:{}".format(vcode))

    def __get_vk_code(self, vk_name):
        if len(vk_name) == 1 and vk_name.isalpha():
            vk_code = self.vk_dict[vk_name.lower()]
        else:
            vk_code = self.vk_dict[vk_name]
        return vk_code

    @staticmethod
    def _Delay(millisecond):
        print("delay", millisecond / 1000, sep=":")
        time.sleep(millisecond / 1000)

    def __press(self, vk_name, n=1):
        vk_code = self.__get_vk_code(vk_name)
        # self.api.M_KeyPress2(self.key_handle, vk_code, n)
        scancode = self._GetScanCodeFromVirtualCode(vk_code)
        for i in range(n):
            self.api.M_KeyDown(self.key_handle, scancode)
            self._Delay(100)
            self.api.M_KeyUp(self.key_handle, scancode)
            self._Delay(250)
        # time.sleep(delay)  # max delay between two M_KeyPress2 is 600ms

    def __press_hot_key(self, key_list, delay=0.3):
        self.api.M_ReleaseAllKey(self.key_handle)
        for key in key_list:
            key_code = self.__get_vk_code(key)
            self.api.M_KeyDown2(self.key_handle, key_code)
        self.api.M_ReleaseAllKey(self.key_handle)
        time.sleep(delay)

    def key(self, key_str, t=0.3):  # A
        # self.log.info("Press key: {}".format(key_str))
        if self.res_dic:
            key = key_str  # 1 #A
            key_change = self.special_dict_revert.get(key_str, key_str)  # True： B false ："A"
            key_string = self.res_dic.get(key_change, key_change)  # True: "Shift+q" false :B
            if key_change == key_string:
                key_str = key
            else:
                key_str = key_string

        try:
            key_list = key_str.split('+')
            length = len(key_list)
            if length == 1:
                if key_str in self.special_dict.keys():
                    value = self.special_dict[key_str]
                    self.__press_hot_key(value.split('+'), t)
                else:
                    self.__press(key_str, 1)
            elif length > 1:
                self.__press_hot_key(key_list, t)
            else:
                print('invalid')
        except Exception as e:
            raise MagicKeyFunctionError(r"Error at press key {}, exception: \n{}".format(key_str, e), self.log)

    def __mui_string_match(self, string):
        indx = 0
        string_li = list(string)
        for i in string_li:
            val = self.res_dic.get(i, i)
            if "shift" in val.lower() and val != i:
                ref = self.special_dict_revert.get(val)
                string_li[indx] = ref
            else:
                string_li[indx] = val
            indx += 1
        string = "".join(string_li)
        return string

    def __check_abs_position(self, x, y):
        rs = self.api.M_ResolutionUsed(self.key_handle, x, y)
        if rs == 0:
            return True
        else:
            return False

    def move_to(self, x, y):
        abs_support = self.__check_abs_position(1600, 900)
        if abs_support:
            self.api.M_MoveTo3(self.key_handle, x, y)
        else:
            print('not support abs')

    def left_click(self, n):
        self.api.M_LeftClick(self.key_handle, n)

    def left_doubleclick(self, n=1):
        self.api.M_LeftDoubleClick(self.key_handle, n)

    def right_click(self, n=1):
        self.api.M_RightClick(self.key_handle, n)

    def mui_vk_prepare(self, path=""):
        if path:
            self.res_dic = YamlOperator(path).read()
        else:
            self.res_dic = {}
        return
