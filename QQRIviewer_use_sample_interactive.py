# please run "python -i QQRIviewer_use_sample_interactive.py"
from PyQt5.QtWidgets import QApplication
import QQRIviewer as qv

app = QApplication([])
qqri = qv.QqriWindow()
qqri.show()
qqri.raise_()

