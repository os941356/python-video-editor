import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, 
                             QSlider, QHBoxLayout, QStyle, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from moviepy.editor import VideoFileClip

class VideoSaveThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, videoClip, start_time, end_time, output_file):
        super().__init__()
        self.videoClip = videoClip
        self.start_time = start_time
        self.end_time = end_time
        self.output_file = output_file

    def run(self):
        clip = self.videoClip.subclip(self.start_time, self.end_time)
        total_frames = clip.fps * (self.end_time - self.start_time)

        def update_progress(get_frame, t):
            current_frame = int(t * clip.fps)
            self.progress.emit(int((current_frame / total_frames) * 100))
            return get_frame(t)

        clip = clip.fl(update_progress)
        clip.write_videofile(self.output_file)

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.videoFilePath = ""
        self.initUI()
        self.videoClip = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.startTime = 0
        self.endTime = 0

    def initUI(self):
        self.setWindowTitle('影片剪輯器')
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel('選擇影片文件:', self)
        self.label.setAlignment(Qt.AlignCenter)
        
        self.openButton = QPushButton('選擇影片', self)
        self.openButton.clicked.connect(self.openFile)

        self.videoLabel = QLabel(self)
        self.videoLabel.setAlignment(Qt.AlignCenter)

        self.startSlider = QSlider(Qt.Horizontal, self)
        self.startSlider.setRange(0, 100)
        self.startSlider.sliderMoved.connect(self.updateStart)

        self.endSlider = QSlider(Qt.Horizontal, self)
        self.endSlider.setRange(0, 100)
        self.endSlider.sliderMoved.connect(self.updateEnd)

        self.playButton = QPushButton(self)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.playVideo)

        self.saveButton = QPushButton('保存剪輯影片', self)
        self.saveButton.clicked.connect(self.saveFile)

        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.openButton)
        layout.addWidget(self.videoLabel)
        layout.addWidget(self.startSlider)
        layout.addWidget(self.endSlider)
        layout.addWidget(self.playButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.progressBar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def openFile(self):
        options = QFileDialog.Options()
        self.videoFilePath, _ = QFileDialog.getOpenFileName(self, "選擇影片文件", "", "影片文件 (*.mp4 *.avi *.mov);;所有文件 (*)", options=options)
        if self.videoFilePath:
            self.label.setText(f'選擇的文件: {self.videoFilePath}')
            self.videoClip = VideoFileClip(self.videoFilePath)
            self.startSlider.setRange(0, int(self.videoClip.duration))
            self.endSlider.setRange(0, int(self.videoClip.duration))
            self.endSlider.setValue(int(self.videoClip.duration))
            self.displayFrame(0)
            self.videoLabel.setFixedSize(self.videoClip.size[0], self.videoClip.size[1])

    def displayFrame(self, time):
        if self.videoClip:
            frame = self.videoClip.get_frame(time)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            height, width, channel = frame.shape
            bytesPerLine = 3 * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            self.videoLabel.setPixmap(QPixmap.fromImage(qImg))

    def updateStart(self, position):
        self.displayFrame(position)
        self.startTime = position

    def updateEnd(self, position):
        self.displayFrame(position)
        self.endTime = position

    def playVideo(self):
        self.timer.start(30)

    def nextFrameSlot(self):
        if self.videoClip:
            currentTime = self.startSlider.value() + 0.03
            if currentTime >= self.endSlider.value():
                self.timer.stop()
            self.startSlider.setValue(currentTime)
            self.displayFrame(currentTime)

    def saveFile(self):
        if self.videoFilePath:
            outputFile, _ = QFileDialog.getSaveFileName(self, "保存剪輯影片", "", "影片文件 (*.mp4 *.avi *.mov);;所有文件 (*)")
            if outputFile:
                self.progressBar.setValue(0)
                self.saveThread = VideoSaveThread(self.videoClip, self.startSlider.value(), self.endSlider.value(), outputFile)
                self.saveThread.progress.connect(self.updateProgress)
                self.saveThread.start()

    def updateProgress(self, value):
        self.progressBar.setValue(value)
        if value == 100:
            self.label.setText('影片已保存')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoEditor()
    ex.show()
    sys.exit(app.exec_())
