from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QFileDialog, QVBoxLayout, QWidget, QMenu, QAction, QApplication
)
from PyQt5.QtGui import QPixmap, QKeySequence, QTransform
from PyQt5.QtCore import Qt, QSize, QTimer, QEasingCurve, QPropertyAnimation, pyqtProperty
import os
import sys
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.svg', '.ico']

class PhotoViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('开源看图软件')
        self.setGeometry(100, 100, 800, 600)
        self.setAcceptDrops(True)  # 开启拖拽功能

        # 窗口属性设置
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinMaxButtonsHint)

        # Create a main widget to hold the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create the layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Image label for displaying the image
        self.image_label = QLabel('请拖拽或打开一张图片')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(self.image_label)

        self.image_list = []
        self.current_index = -1
        self._current_scale = 1.0
        self.image_position = (0, 0)  # 用来存储图片位置
        self.original_width = 0
        self.original_height = 0
        self.rotation_angle = 0

        # Animation for smooth scaling
        self.scale_animation = QPropertyAnimation(self, b"current_scale")
        self.scale_animation.setEasingCurve(QEasingCurve.OutQuart)  # Smooth easing curve
        self.scale_animation.setDuration(150)  # Duration for animation in ms
        self.scale_animation.valueChanged.connect(self.update_image)

    @pyqtProperty(float)
    def current_scale(self):
        return self._current_scale

    @current_scale.setter
    def current_scale(self, value):
        self._current_scale = value
        self.update_image()

    def update_image(self):
        if self.original_width > 0 and self.original_height > 0:
            try:
                pixmap = QPixmap(self.image_list[self.current_index])
                if pixmap.isNull():
                    raise ValueError(f"无法加载图片: {self.image_list[self.current_index]}")
                
                # Apply rotation
                transform = QTransform().rotate(self.rotation_angle)
                rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)

                scaled_pixmap = rotated_pixmap.scaled(
                    QSize(
                        int(self.original_width * self.current_scale),
                        int(self.original_height * self.current_scale)
                    ), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setAlignment(Qt.AlignCenter)
            except Exception as e:
                logger.error(f"更新图片时出错：{str(e)}")
                self.image_label.setText(f'图片更新失败：{str(e)}')

    ### 📂 **打开图片或文件夹** ###
    def open_image_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if folder_path:
            self.image_list = self.scan_images_recursive(folder_path)
            if self.image_list:
                self.current_index = 0
                self.display_image()

    def scan_images_recursive(self, folder):
        image_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if os.path.splitext(file)[1].lower() in SUPPORTED_FORMATS:
                    image_files.append(os.path.join(root, file))
        return image_files

    ### 🖼️ **显示图片** ###
    def display_image(self):
        if not self.image_list:
            self.image_label.setText('没有可显示的图片')
            return

        if 0 <= self.current_index < len(self.image_list):
            try:
                pixmap = QPixmap(self.image_list[self.current_index])
                if pixmap.isNull():
                    raise ValueError(f"无法加载图片: {self.image_list[self.current_index]}")
                
                # Store original dimensions
                self.original_width = pixmap.width()
                self.original_height = pixmap.height()

                # Apply rotation
                transform = QTransform().rotate(self.rotation_angle)
                rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)

                # Pre-scale the image to avoid loading very large images into memory
                pre_scaled_pixmap = rotated_pixmap.scaled(self.image_label.size() * 2, Qt.KeepAspectRatio, Qt.FastTransformation)
                self.image_label.setPixmap(pre_scaled_pixmap)
                self.image_label.setAlignment(Qt.AlignCenter)

                # Reset scale for new image
                self.current_scale = 1.0
            except Exception as e:
                logger.error(f"显示图片时出错：{str(e)}")
                self.image_label.setText(f'图片加载失败：{str(e)}')
        else:
            self.image_label.setText('没有更多图片')

    ### ◀️▶️ **图片导航** ###
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_image()

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.display_image()

    ### 🔍 **缩放** ###
    def zoom_in(self):
        # Smaller increment for smoother scaling
        if self.current_scale < 100.0:
            new_scale = min(self.current_scale + 0.05, 100.0)  # Smaller step for smoother feel
            self.scale_animation.setStartValue(self.current_scale)
            self.scale_animation.setEndValue(new_scale)
            self.scale_animation.start()

    def zoom_out(self):
        if self.current_scale > 0.2:
            new_scale = max(self.current_scale - 0.05, 0.2)  # Smaller step for smoother feel
            self.scale_animation.setStartValue(self.current_scale)
            self.scale_animation.setEndValue(new_scale)
            self.scale_animation.start()

    ### 🔄 **旋转图片** ###
    def rotate_image(self):
        self.rotation_angle = (self.rotation_angle + 45) % 360  # 45度旋转，每次增加45度
        self.display_image()

    ### 🚚 **拖拽功能** ###
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.splitext(file_path)[1].lower() in SUPPORTED_FORMATS:
                self.image_list = [file_path]
                self.current_index = 0
                self.display_image()
                break

    ### 🎹 **键盘控制** ###
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Left):
            self.prev_image()
        elif event.key() in (Qt.Key_Down, Qt.Key_Right):
            self.next_image()
        elif event.key() == Qt.Key_Plus:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_R:
            self.rotate_image()
        else:
            super().keyPressEvent(event)

    ### 🖱️ **鼠标事件** ###
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # Drag the image within the label
            delta = event.pos() - self.last_pos
            self.image_position = (self.image_position[0] + delta.x(), self.image_position[1] + delta.y())
            self.image_label.move(self.image_position[0], self.image_position[1])
            self.last_pos = event.pos()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_image_folder()

    ### 🖱️ **右键菜单** ###
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        copy_location_action = QAction('复制图片位置', self)
        copy_location_action.triggered.connect(self.copy_image_location)
        context_menu.addAction(copy_location_action)
        context_menu.exec_(event.globalPos())

    ### 📍 **复制图片位置到剪贴板** ###
    def copy_image_location(self):
        if self.image_list and 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]
            clipboard = QApplication.clipboard()
            clipboard.setText(image_path)  # 将图片路径复制到剪贴板
            self.image_label.setText(f'图片位置已复制: {image_path}')
        else:
            self.image_label.setText('没有可复制的图片位置')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PhotoViewer()
    viewer.show()
    sys.exit(app.exec_())