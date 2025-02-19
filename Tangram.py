# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 16:20:31 2024

@author: USER
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import cv2 as cv
import numpy as np
import random
import os
import sys
import threading
import time
from inference import get_roboflow_model
import supervision as sv

first_ui = uic.loadUiType("C:/Users/USER/Desktop/Deep_learning/tangram/mainwindow.ui")[0]
second_ui = uic.loadUiType("C:/Users/USER/Desktop/Deep_learning/tangram/mainwindow2.ui")[0]

# 두번째 UI 화면 출력
class second(QMainWindow,second_ui):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Tangramplay")
         
        self.modelBtn.clicked.connect(self.captureFunction)         
        self.cameraBtn.clicked.connect(self.videoFunction)
        self.matchBtn.clicked.connect(self.startFunction)
        self.exitBtn.clicked.connect(self.quitFunction)
        
        self.image_folder_path = "C:/Users/USER/Desktop/Deep_learning/dataset/class"
        self.load_img()

        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("background-color: white; border: 1px solid black;")
        
        self.accuracy_label.setAlignment(Qt.AlignCenter)
        self.accuracy_label.setStyleSheet("background-color: white; border: 1px solid black;")
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_callback)
        self.time_left = 5
        self.btn_press_count = 0
        self.sift = cv.SIFT_create()
        self.model_img = None
        self.frame = None

        self.model_label = QLabel(self)
        self.model_label.setGeometry(350, 20, 550, 530)
        self.model_label.setAlignment(Qt.AlignCenter)
        self.model_label.setStyleSheet("border: 1px solid black;")
    
    # 이미지 파일 로드
    def load_img(self): 
        self.template_img = []
        for filename in os.listdir(self.image_folder_path):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                img_path = os.path.join(self.image_folder_path, filename)
                self.template_img.append(img_path)

    # 이미지 랜덤 선택  
    def captureFunction(self): 
        random_img = random.choice(self.template_img)
        self.model_img = cv.imread(random_img)
        pixmap = QPixmap(random_img)
        self.model_label.setPixmap(pixmap)
        self.accuracy_label.setText("")

    # 웹캠 화면 실행
    def videoFunction(self):
        self.cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        if not self.cap.isOpened():
            self.close()         
        while True:
            ret, self.frame = self.cap.read() 
            if not ret:
                break 
   
            cv.imshow('display',self.frame)
            key = cv.waitKey(1)
            if key == ord('q'): break
        cv.destroyAllWindows() 
            
    # 매칭 시작
    def startFunction(self):
        self.start_timer()

    # 타이머 시작
    def start_timer(self):
        if self.timer is not None:
            self.timer.stop()
        self.timer = Timer(interval=15, callback=self.timer_callback)  # 10초로 설정
        self.timer.start()

    # 타이머 출력
    def timer_callback(self, count):
        self.timer_label.setText(f"{count:.1f} sec")

        if count <= 0.1:
            self.matchFunction()

    # 랜덤 이미지 출력
    def randomImgFunction(self):
        random_image = random.choice(self.template_img)
        self.model_img = cv.imread(random_image)
        cv.imshow('Random Image', self.model_img)
    
    # 학습모델을 이용한 매칭 수행 및 결과 출력
    def matchFunction(self):
        if self.model_img is None:
            print("모델 이미지 선택")
            return
        
        model = get_roboflow_model(model_id="tangram_real_final/1", api_key='WqWJKXlwqRlu1FiuMjdY')
        results = model.infer(self.frame)[0]
        
        detections = sv.Detections.from_inference(results)
        
        bounding_box_annotator = sv.BoundingBoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        precision = round(detections.confidence[0], 2) * 100
        
        # annotate the image with our inference results
        annotated_image = bounding_box_annotator.annotate(
            scene=self.frame, detections=detections)
        annotated_image = label_annotator.annotate(
            scene=annotated_image, detections=detections)

        # display the image
        sv.plot_image(annotated_image)
        
        if precision > 90:
            self.accuracy_label.setText(f'정답!  정확도 : {precision}%')
        else:
            self.accuracy_label.setText(f'오답.. 정확도 : {precision}%')
    
    # 실행 종료
    def quitFunction(self):
        self.cap.release()
        cv.destroyAllWindows()
        if self.timer is not None:
            self.timer.stop()
        self.close()

# 첫번째 UI 화면 출력    
class first(QMainWindow,first_ui) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Main")
        self.startBtn.clicked.connect(self.second_window)
    
    def second_window(self):
        self.window2 = second()
        self.window2.show()

# 타이머 클래스 구현
class Timer:
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.is_running = False
        self.thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def stop(self):
        self.is_running = False
        self.reset()

    def _run(self):
        count = self.interval
        while count >= 0 and self.is_running:
            self.callback(count)
            time.sleep(0.1)
            count -= 0.1

    def reset(self):
        self.thread = None

# 어플리케이션 실행
app = QApplication(sys.argv)
win = first()
win.show()
app.exec_()