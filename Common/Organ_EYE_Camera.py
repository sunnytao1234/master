import os

import cv2

from Common import Kernel_ERROR
from Common.log import log


class Eye:
    def __init__(self, n):
        """
        :param n: <class 'int'>, n is the number of the camera
        """
        self.property = 'Eye'
        self.log = log
        memory_path = os.path.join(os.getcwd(), 'Test_Data', 'Memory')
        self.memory = memory_path + '\\' + str(n)
        if not os.path.exists(self.memory):
            os.makedirs(self.memory)
        self.memory_view = self.memory + '\\View.png'
        self.memory_view_jpg = self.memory + '\\View.jpg'  # video capture card
        self.memory_views = self.memory + '\\Views.avi'
        self.cap = cv2.VideoCapture(n, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.eye = n

    def snapshot(self):
        try:
            ret, img = self.cap.read()
            cv2.imwrite(self.memory_view, img)
            return self.memory_view
        except Exception:
            raise Kernel_ERROR.EyeFunctionError()

    def views(self, t):
        try:
            if os.path.exists(self.memory_views):
                os.remove(self.memory_views)
            four_cc = cv2.VideoWriter_fourcc(*'XVID')
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            v_out = cv2.VideoWriter(self.memory_views, four_cc, fps, size)
            lt = t * fps
            frames = 0
            while frames < lt:
                ret, img = self.cap.read()
                v_out.write(img)
                frames += 1
            v_out.release()
            return self.memory_views
        except Exception:
            raise Kernel_ERROR.EyeFunctionError()
