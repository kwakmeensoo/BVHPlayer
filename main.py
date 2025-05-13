import sys
from render import Renderer
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    width = 1280
    height = 720

    qt_app = QApplication(sys.argv)

    renderer = Renderer(width, height, "BVH Player")

    renderer.run()