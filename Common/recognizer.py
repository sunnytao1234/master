import os

from PIL import Image, ImageOps

from Common.common import is_controller
from Common.log import log


# from Test_Script import ocr_client


def picture_gray():
    """
    Grayscale the picture
    :return:
    """
    # to do


if is_controller():
    import pytesseract
"""
need install tesseract-ocr-w64-v5.0.0.exe
path:\\15.83.240.98\Automation\tools\tesseract-ocr-w64-v5.0.0.exe
"""

if is_controller():
    file_ver4 = r'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
    file_ver5 = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
    for file in [file_ver4, file_ver5]:
        if os.path.exists(file):
            # pytesseract.pytesseract.tesseract_cmd = r'C://Program Files/Tesseract-OCR/tesseract.exe'
            break
    else:
        raise FileNotFoundError


def recognize_string(pic_path, lang='eng'):
    """
    Recognize characters in picture according to different lang parameters.
    :param pic_path: Full path of picture.
    :param lang: candidate value: 'automation3', 'eng', ''
    :return: A list of recognized characters.
    """
    log.info('Start recognizing string in picture')
    t_list = []
    pic = pic_path
    if lang:
        try:
            image = Image.open(pic)
            gray = image.convert('L')
            invert_pic = ImageOps.invert(gray)
            pytesseract.pytesseract.tesseract_cmd = r'C://Program Files/Tesseract-OCR/tesseract.exe'
            text = pytesseract.image_to_string(invert_pic, lang='eng')  # lang=automation3, lang=eng
            log.info('[recognize_string]text: \n{}\n'.format(text))
            t_list = text.split('\n')
            t_list = [i for i in t_list if i != '']
        except Exception as e:
            log.info('[recognizer][recognize_string]error occurs when recognize string from picture.\n{}'.format(e))
        finally:
            return t_list
    else:
        try:
            res = ocr_client.get_results(image_path=pic_path)
            log.info('ocr_client get result: {}'.format(res))
            for k, v in res.items():
                if k == 'labels':
                    t_list = v
                    break
        except Exception as e:
            log.info('[recognizer][recognize_string]error occurs when use ocr client to recognize string from '
                     'picture.\n{}'.format(e))
        finally:
            return t_list


def security_code(pic_path):
    code = ''
    text_list = recognize_string(pic_path)
    if not text_list:
        return code
    for t in text_list:
        if 'ENTER' in t:
            code = t.strip().split()[0]
            break
    else:
        log.info('[get_security_code]fail to find security code in picture.')
    return code


def __deal_with_specific_characters(lst):
    for i in lst:
        if 'IPV' in i.upper():
            i_new = i.replace(i[4], '')
            i_new = i_new.replace(i_new.split(' ')[4], '')
            lst[lst.index(i)] = i_new
    return lst


def f10_boot_order_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    start = ''
    end = ''
    for item in lst:
        if 'UEFI BOOT SOURCES' in item.upper():
            start = lst.index(item) + 1
        elif 'LEGACY BOOT SOURCES' in item.upper():
            end = lst.index(item)
    if start and end:
        log.debug('origin boot sources: {}'.format(lst[start: end]))
        dealed_lst = __deal_with_specific_characters(lst[start: end])
        dic['UEFI Boot Sources'] = dealed_lst
        return dic
    else:
        log.error('Fail to get f10_boot_order list.')
        return False


def secure_boot_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    for item in lst:
        if 'LEGACY SUPPORT' in item.upper():
            dic['Legacy Support'] = item.split()[-1][1:]
        if 'SECURE BOOT ENABLE' in item.upper() or 'SECURE BOOT DISABLE' in item.upper():
            # if 'Secure Boot' in string and 'Configuration' not in string and "Don't clear" not in string:
            dic['Secure Boot'] = item.split()[-1]
    return dic


def usb_port_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    for item in lst:
        if 'FRONT USB PORTS' in item.upper():
            dic['Front USB Ports'] = item.split()[-1][1:]
    return dic


def s5_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    for item in lst:
        # if 'S5' in item.upper():
        if 'MAXIMUM POWER' in item.upper():
            dic['S5 Maximum Power Savings'] = item.split()[-1][1:]
    return dic


def bios_power_on_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    for item in lst:
        if 'SUNDAY' in item.upper():
            dic['Sunday'] = item.split()[-1][1:]
        elif 'MONDAY' in item.upper():
            dic['Monday'] = item.split()[-1]
    return dic


def integrated_graphics_uma(pic_path):
    dic = {}
    lst = recognize_string(pic_path)
    if not lst:
        return dic
    for item in lst:
        if 'INTEGRATED GRAPHICS' in item.upper():
            dic['Integrated Graphics'] = item.split()[-1][1:]
        elif 'UMA' in item.upper():
            dic['UMA'] = item.split()[-1]
    return dic


def down_times_for_ipv6(pic_path):
    times = 0
    boot_order = f10_boot_order_dic(pic_path)
    if boot_order:
        for item in boot_order['UEFI Boot Sources']:
            if 'IPV6' in item.upper():
                times = boot_order['UEFI Boot Sources'].index(item) + 1
                break  # get the first IPV6
    else:
        log.error('[recognizer][down_times_for_ipv6]Fail to get boot order.')
    return times


def down_times_for_device_options(pic_path):
    times = 0
    start = ''
    end = ''
    lst = recognize_string(pic_path)
    if lst:
        for item in lst:
            if 'IOS POWER' in item.upper():
                start = lst.index(item)
            elif 'DEVICE OPTIONS' in item.upper():
                end = lst.index(item)
    else:
        log.error('[recognizer][down_times_for_device_options]Fail to get string list for Advanced menu.')
    if start and end:
        times = end - start
    return times


def set_legacy_secure_boot(pic_path):
    operation_list = []
    legacy_secure_boot = secure_boot_dic(pic_path)
    # if legacy_secure_boot == {'Legacy Support': 'Disable', 'Secure Boot': 'Enable'}:
    if 'Disable' in legacy_secure_boot['Legacy Support'] and 'Enable' in legacy_secure_boot['Secure Boot']:
        operation_list = ['Down', 'Right', 'F10']
    # elif legacy_secure_boot == {'Legacy Support': 'Disable', 'Secure Boot': 'Disable'}:
    elif 'Disable' in legacy_secure_boot['Legacy Support'] and 'Disable' in legacy_secure_boot['Secure Boot']:
        operation_list = ['Right', 'F10']
    # elif legacy_secure_boot == {'Legacy Support': 'Enable', 'Secure Boot': 'Disable'}:
    elif 'Enable' in legacy_secure_boot['Legacy Support'] and 'Disable' in legacy_secure_boot['Secure Boot']:
        operation_list = ['Right', 'Enter', 'F10']
    else:
        log.error('Invalid legacy_secure_boot.\n{}\n'.format(legacy_secure_boot))
    return operation_list


def set_integrated_graphics_and_uma(pic_path):
    inte_graphics_uma = integrated_graphics_uma(pic_path)
    if inte_graphics_uma['Integrated Graphics'] == 'Auto':
        operation_list = ['Right', 'Down', 'Right', 'F10']
    else:
        operation_list = ['Right', 'F10']
    return operation_list


def f9_boot_sources_dic(pic_path):
    dic = {}
    lst = recognize_string(pic_path, lang='')
    if not lst:
        return dic
    start = ''
    end = ''
    for item in lst:
        if 'UEFI BOOT SOURCES' in item.upper():
            start = lst.index(item) + 1
        # elif 'LEGACY BOOT SOURCES' in item.upper():
        #     end = lst.index(item)
    # if start and end:
    if start:
        log.debug(lst[start:])
        dic['Boot Sources'] = lst[start:]
        return dic
    else:
        log.error('Fail to get f9_boot_sources_dic.')
        return False


def down_times_for_f9_boot_sources(pic_path, selection):
    """
    Calculate the times for pressing down according to the position of key words.
    :param pic_path: path for captured picture.
    :param selection: candidate value: 'INDOWS BOOT MANAGER', 'KINGSTON'
    :return: pressing down times. int
    """
    times = 0
    result = f9_boot_sources_dic(pic_path)
    if not result:
        return False
    boot_source_list = result['Boot Sources']
    for item in boot_source_list:
        if selection in item.upper():
            times = boot_source_list.index(item) + 1
            break
    return times


def up_times_for_flash_system_bios(pic_path):
    times = 0
    start = ''
    end = ''
    lst = recognize_string(pic_path)
    if lst:
        for item in lst:
            if 'FLASH SYSTEM' in item.upper():
                start = lst.index(item)
            elif 'SAVE CHANGES AND EXIT' in item.upper():
                end = lst.index(item)
    else:
        log.error('[recognizer][up_times_for_flash_system_bios]Fail to get string list.')
    if start and end:
        times = end - start
    return times


def up_times_for_system_ids(pic_path):
    times = 0
    start = ''
    end = ''
    lst = recognize_string(pic_path)
    if lst:
        for item in lst:
            if 'SYSTEM IDS' in item.upper():
                start = lst.index(item)
            elif 'SECURE BOOT CONFIGURATION' in item.upper():
                end = lst.index(item)
    else:
        log.error('[recognizer][down_times_for_system_ids]Fail to get string list for Security menu.')
    if start and end:
        times = end - start
    return times + 1


def down_times_for_password_option(pic_path):
    times = 0
    start = ''
    end = ''
    lst = recognize_string(pic_path)
    if lst:
        for item in lst:
            if 'SETUP PASSWORD' in item.upper():
                start = lst.index(item)
            elif 'PASSWORD OPTION' in item.upper():
                end = lst.index(item)
    else:
        log.error('[recognizer][down_times_for_password_option]Fail to get string list for Security menu.')
    if start and end:
        times = end - start
    return times


def __deal_with_item(item):
    # item = item[item.index('[') + 1:item.index(']')]
    # item = item[item.index('[') + 1:].strip(']')
    return item


# def __deal_with_item(item):
#     item = item.replace('[', '').replace(']', '')
#     return item


def system_ids_dic(pic_path):
    dic_not_empty = {}
    dic_others = {}
    lst = recognize_string(pic_path)
    if not lst:
        log.error('[recognizer][system_ids_dic]Fail to recognize string.')
        return dic_not_empty, dic_others
    for item in lst:
        if 'UUID' in item.upper():
            item = __deal_with_item(item)
            dic_not_empty['UUID'] = item
        elif 'FAMILY NAME' in item.upper():
            item = item.replace('Family Name ', '')
            dic_not_empty['Family Name'] = item
        elif 'ASSET' in item.upper():
            item = __deal_with_item(item)
            dic_others['Asset'] = item
        elif 'OWNERSHIP TAG' in item.upper():
            item = __deal_with_item(item)
            dic_others['Ownership Tag'] = item
        elif 'SERIAL NUMBER' in item.upper():
            item = __deal_with_item(item)
            dic_others['Serial Number'] = item
        elif 'PRODUCT NAME' in item.upper():
            item = __deal_with_item(item)
            dic_others['Product Name'] = item
        elif 'SKU NUMBER' in item.upper():
            item = __deal_with_item(item)
            dic_others['SKU Number'] = item
        elif 'BUILD ID' in item.upper():
            item = __deal_with_item(item)
            dic_others['Build ID'] = item
        elif 'FEATURE BYTE' in item.upper():
            item = item.replace('Feature Byte ', '')
            dic_others['Feature Byte'] = item
    return dic_not_empty, dic_others


def system_ids_dic(pic_path):
    dic_not_empty = {}
    dic_others = {}
    lst = recognize_string(pic_path)
    if not lst:
        log.error('[recognizer][system_ids_dic]Fail to recognize string.')
        return dic_not_empty, dic_others
    for item in lst:
        if 'UUID' in item.upper():
            # item = __deal_with_item(item)
            dic_not_empty['UUID'] = item
        elif 'FAMILY NAME' in item.upper():
            # item = item.replace('Family Name ', '')
            dic_not_empty['Family Name'] = item
        elif 'ASSET TRACKING NUMBER' in item.upper():
            # item = __deal_with_item(item)
            dic_others['Asset'] = item
        elif 'OWNERSHIP TAG' in item.upper():
            # item = __deal_with_item(item)
            dic_others['Ownership Tag'] = item
        elif 'SERIAL NUMBER' in item.upper():
            # item = __deal_with_item(item)
            dic_others['Serial Number'] = item
        elif 'PRODUCT NAME' in item.upper():
            # item = __deal_with_item(item)
            dic_others['Product Name'] = item
        elif 'SKU NUMBER' in item.upper():
            # item = __deal_with_item(item)
            dic_others['SKU Number'] = item
        elif 'BUILD ID' in item.upper():
            # item = __deal_with_item(item)
            dic_others['Build ID'] = item
        elif 'FEATURE BYTE' in item.upper():
            # item = item.replace('Feature Byte ', '')
            dic_others['Feature Byte'] = item
    return dic_not_empty, dic_others


def usb_identifier_in_efi(pic_path):
    identifier = ''
    text_list = recognize_string(pic_path, lang='')
    if not text_list:
        return identifier
    for t in text_list:
        if 'REMOVABLE' in t.upper():
            identifier = text_list[text_list.index(t) - 1]
            identifier = (identifier[:2].replace('h', 'b').replace('1', 'l', 1) + identifier[2:]).replace('.', '')
            break
    else:
        log.info('[get_security_code]fail to find security code in picture.')
    return identifier


def up_times_for_usb_security(pic_path):
    times = 0
    start = ''
    end = ''
    lst = recognize_string(pic_path)
    if lst:
        for item in lst:
            if 'USB SECURITY' in item.upper():
                start = lst.index(item)
            elif 'SECURE BOOT CONFIGURATION' in item.upper():
                end = lst.index(item)
    else:
        log.error('[recognizer][up_times_for_usb_security]Fail to get string list for Security menu.')
    if start and end:
        times = end - start
    return times


if __name__ == '__main__':
    picture = r'C:\Users\linlen\Desktop\settings in F10\f9_540_linux.jpg'
    re = recognize_string(picture, lang='eng')
    print(re)
