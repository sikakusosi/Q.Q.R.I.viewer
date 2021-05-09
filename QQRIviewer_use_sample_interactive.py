from PyQt5.QtWidgets import QApplication
import QQRIviewer as qv

app = QApplication([])
qqri = qv.QqriWindow()
qqri.show()
qqri.raise_()

