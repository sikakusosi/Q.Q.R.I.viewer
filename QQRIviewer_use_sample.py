import numpy as np
from PIL import Image, ImageFile

import QQRIviewer as qv

qqri = qv.QqriWindow()
qqri.show()
target_img2 = np.array(Image.open('lena_bw.tiff')).astype(float)
qqri.overwrite_imageview(['lena.tiff', target_img2])



