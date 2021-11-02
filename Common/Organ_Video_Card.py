import os
import platform
import sys
import threading
import time
from ctypes import *

from PyQt5 import QtWidgets

from Common import ui_automation
from Common.common import OSTool
from Common.common_function import get_current_dir
from Common.log import log


class QWindow(QtWidgets.QWidget):
    signal = 0
    device0 = c_void_p(0)
    dll_p = get_current_dir("Test_Utility")
    os.environ['path'] += ';{}'.format(dll_p)
    bit = platform.architecture()[0]
    print(bit)
    if bit == '32bit':
        print(get_current_dir('Test_Utility', 'QCAP.X86.DLL'))
        QCAP = CDLL(get_current_dir('Test_Utility', 'QCAP.X86.DLL'))
        print(QCAP)
    else:
        QCAP = CDLL(get_current_dir('Test_Utility', 'QCAP.X64.DLL'))

    video_port = 2
    pic_memory_path = get_current_dir('Test_Data', 'video_card')
    pic_name = pic_memory_path + r'/view.jpg'
    if not os.path.exists(pic_memory_path):
        os.makedirs(pic_memory_path)
    m_nVideoWidth = c_ulong(0)
    m_nVideoHeight = c_ulong(0)
    m_dVideoFrameRate = c_double(0.0)
    m_nAudioChannels = c_ulong(0)
    m_nAudioBitsPerSample = c_ulong(0)
    m_nnAudioSampleFrequency = c_ulong(0)
    m_startrecord = False

    # Create the C callable callback
    PF_NO_SIGNAL_DETECTED_CALLBACK = CFUNCTYPE(c_ulong, c_void_p, c_long, c_long, c_void_p)
    PF_SIGNAL_REMOVED_CALLBACK = CFUNCTYPE(c_ulong, c_void_p, c_long, c_long, c_void_p)
    PF_FORMAT_CHANGED_CALLBACK = CFUNCTYPE(c_ulong, c_void_p, c_ulong, c_ulong, c_ulong, c_ulong, c_int, c_double,
                                           c_ulong,
                                           c_ulong, c_ulong, c_void_p)
    PF_VIDEO_PREVIEW_CALLBACK = CFUNCTYPE(c_ulong, c_void_p, c_double, c_void_p, c_ulong, c_void_p)
    PF_AUDIO_PREVIEW_CALLBACK = CFUNCTYPE(c_ulong, c_void_p, c_double, c_void_p, c_ulong, c_void_p)

    QCAP_START_RECORD = CFUNCTYPE(c_ulong, c_void_p, c_uint, c_char_p, c_ulong, c_double, c_double, c_double, c_ulong,
                                  c_char_p)

    def __init__(self):
        log.info("%r" % super(QWindow, self))
        super(QWindow, self).__init__()
        self.setWindowTitle("Preview")
        self.setGeometry(0, 0, 1024, 650)

        def on_no_signal_detected(pDevice, nVideoInput, nAudioInput, pUserData):
            log.info("------------no signal detected callback----------------")
            print(nVideoInput)
            QWindow.signal = 0
            return 0

        def on_signal_removed(pDevice, nVideoInput, nAudioInput, pUserData):
            QWindow.signal = 0
            print(QWindow.signal)
            log.info("------------signal removed callback----------------")
            return 0

        def on_format_changed(pDevice, nVideoInput, nAudioInput, nVideoWidth, nVideoHeight, bVideoIsInterleaved,
                              dVideoFrameRate, nAudioChannels, nAudioBitsPerSample, nAudioSampleFrequency, pUserData):
            log.info("-on_process_format_changed (%d, %d, %d, %d, %d, %f, %d, %d, %d, %r) %s" % (
                nVideoInput, nAudioInput, nVideoWidth, nVideoHeight, bVideoIsInterleaved, dVideoFrameRate,
                nAudioChannels,
                nAudioBitsPerSample, nAudioSampleFrequency, pUserData, self.signal))

            global m_nVideoWidth, m_nVideoHeight, m_dVideoFrameRate, m_nAudioChannels, m_nAudioBitsPerSample, m_nnAudioSampleFrequency

            if nVideoWidth != 0 and nVideoHeight != 0:
                m_nVideoWidth = nVideoWidth
                m_nVideoHeight = nVideoHeight
                m_dVideoFrameRate = dVideoFrameRate
                m_nAudioChannels = nAudioChannels
                m_nAudioBitsPerSample = nAudioBitsPerSample
                m_nnAudioSampleFrequency = nAudioSampleFrequency

            return 0

        def on_video_preview(pDevice, dSampleTime, pFrameBuffer, nFrameBufferLen, pUserData):
            QWindow.signal = 1
            return 0

        def on_audio_preview(pDevice, dSampleTime, pFrameBuffer, nFrameBufferLen, pUserData):
            return 0

        self.m_pNoSignalDetectedCB = self.PF_NO_SIGNAL_DETECTED_CALLBACK(on_no_signal_detected)
        self.m_pSignalRemovedCB = self.PF_SIGNAL_REMOVED_CALLBACK(on_signal_removed)
        self.m_pFormatChangedCB = self.PF_FORMAT_CHANGED_CALLBACK(on_format_changed)
        self.m_pVideoPreviewCB = self.PF_VIDEO_PREVIEW_CALLBACK(on_video_preview)
        self.m_pAudioPreviewCB = self.PF_AUDIO_PREVIEW_CALLBACK(on_audio_preview)

        # strName = "CY3014 USB"  # For UB530
        strName = "UB3300 USB"  # For UB570
        # QCAP.QCAP_CREATE(strName.encode('utf-8'), 0, 0, byref(device0), 0, 0)
        # QCAP.QCAP_CREATE(strName.encode('utf-8'), 0, c_int32(widget.winId()), byref(device0), 1, 0)
        self.QCAP.QCAP_CREATE(strName.encode('utf-8'), 0, c_int32(self.winId()), byref(self.device0), 1, 0)
        # QCAP.QCAP_SET_VIDEO_DEFAULT_OUTPUT_FORMAT(device0, 0x32595559, 1920, 1080, 0, c_double(30.0))
        self.QCAP.QCAP_REGISTER_FORMAT_CHANGED_CALLBACK(self.device0, self.m_pFormatChangedCB, None)
        self.QCAP.QCAP_REGISTER_NO_SIGNAL_DETECTED_CALLBACK(self.device0, self.m_pNoSignalDetectedCB, None)
        self.QCAP.QCAP_REGISTER_SIGNAL_REMOVED_CALLBACK(self.device0, self.m_pSignalRemovedCB, None)
        self.QCAP.QCAP_REGISTER_VIDEO_PREVIEW_CALLBACK(self.device0, self.m_pVideoPreviewCB, None)
        self.QCAP.QCAP_REGISTER_AUDIO_PREVIEW_CALLBACK(self.device0, self.m_pAudioPreviewCB, None)
        # QCAP.QCAP_RUN(device0)
        # port = 2

        self.QCAP.QCAP_SET_VIDEO_INPUT(self.device0, self.video_port)  # For HDMI input
        # QCAP.QCAP_SET_VIDEO_INPUT(device0, 3)  # For DVI-D input
        self.QCAP.QCAP_RUN(self.device0)

    @staticmethod
    def check_video(wnd, port):
        ui_automation.RadioButtonControl(AutomationId=port).SetFocus()
        ui_automation.RadioButtonControl(AutomationId=port).Click()
        time.sleep(3)
        if wnd.Exists():
            print('exist')
            resolution = ui_automation.TextControl(AutomationId='1019').Name
            if 'no' in resolution.lower():
                log.debug('video card not connected cause no signal found')
                return False
            elif '1920 x 0 p' in resolution.lower():
                log.debug('no signal because 1920 x 0 p found ')
                return False
            else:
                print('connected')
                return True
        else:
            print('uvc not launched')
            return False

    def stop(self):
        if self.device0 != 0:
            self.QCAP.QCAP_STOP(self.device0)
            self.QCAP.QCAP_DESTROY(self.device0)
        self.device0 = c_void_p(0)

    def closeEvent(self, event):
        self.stop()
        self.close()

    @classmethod
    def get_signal_input_port(cls):
        os.popen(get_current_dir('Test_Utility', 'UVC.UTILITY.X86_V1.56.EXE'))
        # name: DVI-D 33003  HDMI 33001
        # ID: 1019 UVC Utility
        time.sleep(3)
        wnd = ui_automation.WindowControl(Name='UVC Utility')
        ports = {'HDMI': '33001', 'DVI': '33003'}
        if not cls.check_video(wnd, ports['HDMI']):
            if not cls.check_video(wnd, ports['DVI']):
                log.error('Both HDMI and DVI cannot detect signal')
                sys.exit()
            else:
                cls.port = 3
        if wnd.Exists():
            wnd.Close()

    @classmethod
    def __run(cls):
        log.info("Init snapshot jpg......")
        app = QtWidgets.QApplication(sys.argv)
        vccard = cls()
        vccard.show()
        sys.exit(app.exec_())

    @classmethod
    def show_video(cls):
        log.info('start a window to show uut image video')
        cls.get_signal_input_port()
        t = threading.Thread(target=cls.__run)
        t.start()

    @classmethod
    def snap_shot(cls):
        res = cls.QCAP.QCAP_SNAPSHOT_JPG(QWindow.device0, cls.pic_name.encode('utf-8'), 100, 1, 0)
        log.debug("Snap {} Device: {} Status:{}".format(cls.pic_name, QWindow.device0, res))
        return cls.pic_name


class SnapshotJPG:
    def __init__(self):
        # pythoncom.CoInitialize()
        log.info("Init snapshot jpg......")
        self.quick_capture_card = None
        self.pic_memory_path = OSTool.get_current_dir('Test_Data', 'Memory', 'vcc')
        self.pic_name = self.pic_memory_path + r'\view.jpg'
        if not os.path.exists(self.pic_memory_path):
            os.makedirs(self.pic_memory_path)
        self.hw_type = 'VCC'

    def check_video(self, wnd, port):
        ui_automation.RadioButtonControl(AutomationId=port).Click()
        time.sleep(3)
        if wnd.Exists():
            log.info('UVC Utility window exists.')
            # ui_automation.RadioButtonControl(AutomationId='33001').Click()
            resolution = ui_automation.TextControl(AutomationId='1019').Name
            if 'no' in resolution.lower():
                log.info('[Organ_Video_Capture_Card]not connected')
                return False
            elif '1920 x 0 p' in resolution.lower():
                log.info('[Organ_Video_Capture_Card]no signal')
                return False
            else:
                log.info('[Organ_Video_Capture_Card]connected')
                return True
        else:
            log.error('[Organ_Video_Capture_Card]uvc not launched')
            return False

    def start(self):
        os.popen(OSTool.get_current_dir('Test_Utility', 'UVC.UTILITY.X86_V1.56.EXE'))
        # name: DVI-D 33003  HDMI 33001
        # ID: 1019 UVC Utility
        time.sleep(3)
        wnd = ui_automation.WindowControl(Name='UVC Utility')
        ports = {'HDMI': '33001', 'DVI': '33003'}
        if not self.check_video(wnd, ports['HDMI']):
            if not self.check_video(wnd, ports['DVI']):
                log.error('Both HDMI and DVI cannot detect signal')
                sys.exit()
            else:
                with open('port.txt', 'w') as f:
                    f.write('3')
        else:
            with open('port.txt', 'w') as f:
                f.write('2')
        if wnd.Exists():
            wnd.Close()
        app = QtWidgets.QApplication(sys.argv)
        self.quick_capture_card = QWindow()
        # self.quick_capture_card.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.quick_capture_card.show()
        sys.exit(app.exec_())

    def snapshot(self):
        rs = QWindow.QCAP.QCAP_SNAPSHOT_JPG(QWindow.device0, self.pic_name.encode('utf-8'), 100, 1, 0)
        log.info('[Organ_Video_Capture_Card]snapshot result: {}'.format(rs))  # rs 0 means snapshot working well

    def snapshot_demo(self, pic_name, sub_folder='reproduce_issue_cls'):
        pic_name = self.pic_memory_path + r'\{}\{}'.format(sub_folder, pic_name)
        rs = QWindow.QCAP.QCAP_SNAPSHOT_JPG(QWindow.device0, pic_name.encode('utf-8'), 100, 1, 0)
        log.info('snapshot result: {}'.format(rs))  # rs 0 means snapshot working well
        log.info('Capture {}'.format(pic_name))

    def view(self):
        self.snapshot()
        return self.pic_name

    def stop(self):
        log.info('[SnapshotJPG][stop]Stop vcc card.')
        if QWindow.device0 != 0:
            log.info('[SnapshotJPG][stop]start stop and destroy vcc card.')
            QWindow.QCAP.QCAP_STOP(QWindow.device0)
            QWindow.QCAP.QCAP_DESTROY(QWindow.device0)
        QWindow.device0 = c_void_p(0)
        self.quick_capture_card.close()

    def release(self):
        del self.quick_capture_card
        # pythoncom.CoUninitialize()


if __name__ == '__main__':
    pass
