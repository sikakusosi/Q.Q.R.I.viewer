import sys

import numpy as np
from PIL import Image, ImageFile
from PyQt5.QtWidgets import QApplication

import QQRIviewer as qv

app = QApplication([])
qqri = qv.QqriWindow()
qqri.show()
sys.exit(app.exec_())
