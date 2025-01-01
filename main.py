from PyQt5.QtWidgets import QApplication
from viewer import PhotoViewer
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = PhotoViewer()
    viewer.show()
    sys.exit(app.exec_())
