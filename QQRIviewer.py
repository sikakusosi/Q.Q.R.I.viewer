# 標準ライブラリ
from pathlib import Path
import urllib.parse
import time

# サードパーティーライブラリ
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from scipy import ndimage
from PIL import Image, ImageFile, ImageFilter
from matplotlib.pyplot import get_cmap
import time

def roi_pixel_num(img,axis=None):# axis is dummy
    if img.ndim == 3:
        return [np.shape(img)[0]*np.shape(img)[1],
                np.shape(img)[0]*np.shape(img)[1],
                np.shape(img)[0]*np.shape(img)[1],]
    else:
        return np.shape(img)[0]*np.shape(img)[1]

class RectROI_ID(pg.RectROI):
    """
    どの位置にいるwidgetの、何番目のROI？っていうのを記録しておく RectROI class
    """
    roi_stats_func = {'pixel_num':roi_pixel_num,
                      'mean':np.mean,
                      'std':np.std,
                      'var':np.var,
                      'min':np.min,
                      'max':np.max,
                      }

    def __init__(self, pos, size, centered=False, sideScalers=False, widget_pos=None, id=None, pen=None, roi_color=None, **args):
        pg.ROI.__init__(self, pos, size, removable=True, pen=pen, **args)
        self.WIDGET_POS = widget_pos
        self.ID = id
        self.roi_color = roi_color
        self.addScaleHandle([0, 0], [1, 1])
        self.addScaleHandle([0, 1], [1, 0])
        self.addScaleHandle([1, 0], [0, 1])
        self.addScaleHandle([1, 1], [0, 0])
        self.addScaleHandle([1, 0.5], [0, 0.5])
        self.addScaleHandle([0.5, 1], [0.5, 0])

        # analyze window 関連
        self.roi_hist_plot0 = pg.PlotDataItem(np.array([0, 0, 0]), np.array([0, 0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(255,10,10),width=2))
        self.roi_hist_plot1 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,255,10),width=2))
        self.roi_hist_plot2 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,10,255),width=2))
        self.roi_pos  = [[0,0],[0,0]] #[[y_start,y_end],[x_start,x_end]]
        self.roi_size = [0,0] #[y_size,x_size]
        pass

    def get_ID_widgetpos(self):
        return [self.WIDGET_POS, self.ID]


class InfiniteLine_ID(pg.InfiniteLine):
    """
    どの位置にいるwidgetの、何番目のInfiniteLine？っていうのを記録しておく
    """
    def __init__(self, pos=None, angle=90, pen=None, movable=False, bounds=None,
                 hoverPen=None, label=None, labelOpts=None, span=(0, 1), markers=None,
                 name=None, widget_pos=None, id=None, **args):
        pg.InfiniteLine.__init__(self, pos=pos, angle=angle, pen=pen, movable=movable, bounds=bounds,
                                 hoverPen=hoverPen, label=label, labelOpts=labelOpts, span=span, markers=markers,
                                 name=name)
        self.WIDGET_POS = widget_pos
        self.ID = id

    def get_ID_widgetpos(self):
        return [self.WIDGET_POS, self.ID]

class Binary_img_Dialog(QtWidgets.QDialog):

    def __init__(self, header_byte='0', height='', width='', parent=None):
        self.ok = 0
        super(Binary_img_Dialog, self).__init__(parent)

        self.setWindowTitle("Binary Image Input")
        layout = QtWidgets.QFormLayout()

        self.radio_btn_8bit = QtWidgets.QRadioButton("8bit")
        self.radio_btn_16bit = QtWidgets.QRadioButton("16bit")
        self.radio_btn_16bit.setChecked(True)
        self.radio_btn_32bit = QtWidgets.QRadioButton("32bit")
        self.le_header_byte = QtWidgets.QLineEdit()
        self.le_header_byte.setText(header_byte)
        self.le_img_height  = QtWidgets.QLineEdit()
        self.le_img_height.setText(height)
        self.le_img_width   = QtWidgets.QLineEdit()
        self.le_img_width.setText(width)

        self.le_header_byte.setValidator(QtGui.QIntValidator())
        self.le_img_height.setValidator(QtGui.QIntValidator())
        self.le_img_width.setValidator(QtGui.QIntValidator())

        layout.addRow(QtWidgets.QLabel(' '),self.radio_btn_8bit)
        layout.addRow(QtWidgets.QLabel('Bit width'),self.radio_btn_16bit)
        layout.addRow(QtWidgets.QLabel(' '),self.radio_btn_32bit)
        layout.addRow(QtWidgets.QLabel('Header Size (Bytes)'), self.le_header_byte)
        layout.addRow(QtWidgets.QLabel('Image Height (Pixels)'),self.le_img_height)
        layout.addRow(QtWidgets.QLabel('Image Width (Pixels)'),self.le_img_width)

        self.ok_btn = QtWidgets.QPushButton('OK')
        self.cancel_btn = QtWidgets.QPushButton('cancel')
        self.ok_btn.clicked.connect(self.ok_click)
        self.cancel_btn.clicked.connect(self.cancel_click)
        layout.addRow(self.ok_btn,self.cancel_btn)

        self.setLayout(layout)

    def ok_click(self):
        self.accept()
        pass

    def cancel_click(self):
        self.reject()
        pass

    def getdata(self):
        if self.exec_() == QtWidgets.QDialog.Accepted:
            bit_width = self.radio_btn_8bit.isChecked()*8+self.radio_btn_16bit.isChecked()*16+self.radio_btn_32bit.isChecked()*32
            return bit_width, self.le_header_byte.text(), self.le_img_height.text(), self.le_img_width.text()
        else:
            return 'cancel','cancel','cancel','cancel'

class ch_swap_Dialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        self.ok = 0
        super(ch_swap_Dialog, self).__init__(parent)
        self.setAcceptDrops(True)

        self.setWindowTitle("Enter the path of the image to be swapped.")
        layout = QtWidgets.QFormLayout()

        self.radio_btn_list = []
        self.radio_btn_list.append(QtWidgets.QRadioButton("RGB"))
        self.radio_btn_list.append(QtWidgets.QRadioButton("YUV422(8bit)"))
        self.radio_btn_list.append(QtWidgets.QRadioButton("ITU-R_BT.601(8bit)"))
        self.radio_btn_list.append(QtWidgets.QRadioButton("ITU-R_BT.709(8bit)"))
        self.radio_btn_list[0].setChecked(True)
        for i in np.arange(len(self.radio_btn_list)):
            layout.addRow(self.radio_btn_list[i])

        self.le_path_0ch = QtWidgets.QLineEdit()
        self.le_path_0ch.setText('')
        self.le_path_1ch = QtWidgets.QLineEdit()
        self.le_path_1ch.setText('')
        self.le_path_2ch = QtWidgets.QLineEdit()
        self.le_path_2ch.setText('')
        layout.addRow(QtWidgets.QLabel('0ch path'), self.le_path_0ch)
        layout.addRow(QtWidgets.QLabel('1ch path'), self.le_path_1ch)
        layout.addRow(QtWidgets.QLabel('2ch path'), self.le_path_2ch)

        self.ok_btn = QtWidgets.QPushButton('OK')
        self.cancel_btn = QtWidgets.QPushButton('cancel')
        self.ok_btn.clicked.connect(self.ok_click)
        self.cancel_btn.clicked.connect(self.cancel_click)
        layout.addRow(self.ok_btn,self.cancel_btn)

        self.setLayout(layout)

    def ok_click(self):
        self.accept()
        pass

    def cancel_click(self):
        self.reject()
        pass

    def getdata(self):
        if self.exec_() == QtWidgets.QDialog.Accepted:
            img_format = ''
            for i in np.arange(len(self.radio_btn_list)):
                if self.radio_btn_list[i].isChecked():
                    img_format = self.radio_btn_list[i].text()

            return self.le_path_0ch.text(), self.le_path_1ch.text(), self.le_path_2ch.text(), img_format
        else:
            return 'cancel','cancel','cancel','cancel'

    def dragEnterEvent(self, event):
        event.accept()
    def dragMoveEvent(self, event):
        pass
    def dropEvent(self, event):
        event.accept()
        event.acceptProposedAction()
        print(self.img_path)
        ImageFile.LOAD_TRUNCATED_IMAGES = True



def obc_clamp_set_val(target_img, set_val,raw_mode):
    return target_img-set_val[0]

def obc_clamp_OBarea_val(target_img,OBarea_pos):
    return target_img-np.mean(target_img[int(OBarea_pos[0]):int(OBarea_pos[2]),
                                         int(OBarea_pos[1]):int(OBarea_pos[3])])

def dpc_type1(target_img, dummy,raw_mode):
    return target_img


def generate_gaussian_filter(shape,sigma):
    """
    フィルタの総和が1になる、任意矩形形状のガウシアンフィルタを返す
    generate_gaussian_filter((5,5),0.5) = fspecial('gaussian',5,0.5)<Matlab func>
    例外処理として、sigma=0の場合はshapeはそのまま、値は中心に1のフィルタを返す

    :param shape: タプル、フィルタの(y_size, x_size)。奇数であること
    :param sigma: ガウス関数のシグマ
    :return: フィルタの総和が1になる、任意矩形形状のガウシアンフィルタ
    """
    shape = (int(shape[0]),int(shape[1]))
    if sigma==0:
        temp = np.zeros(shape)
        temp[shape[0]//2,shape[1]//2] = 1
        return temp

    m,n = [(ss-1.0)/2.0 for ss in shape]
    y,x = np.ogrid[-m:m+1,-n:n+1]
    gf = np.exp( -(x*x + y*y) / (2.0*sigma*sigma) )
    gf[ gf < np.finfo(gf.dtype).eps*gf.max() ] = 0
    sum_gf = gf.sum()
    if sum_gf != 0:
        gf = gf/sum_gf
    return gf

def raw_gaussian(target_img,shape_sigma,raw_mode):
    if np.mod(shape_sigma[0],2)==0 or np.mod(shape_sigma[1],2)==0:
        print('warning! RawNR-gaussian : Please input odd number')
        return target_img

    shape_sigma = np.array(shape_sigma).astype(int)
    gf = generate_gaussian_filter((shape_sigma[0],shape_sigma[1]),shape_sigma[2])
    gf_rb = np.zeros((shape_sigma[0],shape_sigma[1]))
    gf_g  = np.zeros((shape_sigma[0],shape_sigma[1]))
    rb_y_start = 1*(np.mod(shape_sigma[0],4)-1)
    rb_x_start = 1*(np.mod(shape_sigma[1],4)-1)
    gf_rb[0::2,0::2] = gf[0::2,0::2]
    gf_g[0::2,0::2] = gf[0::2,0::2]
    gf_g[1::2,1::2] = gf[1::2,1::2]
    gf_rb = gf_rb/np.sum(gf_rb)
    gf_g = gf_g/np.sum(gf_g)

    gf_img = ndimage.convolve(target_img,gf_rb,mode='mirror')
    gf_img2 = ndimage.convolve(target_img,gf_g,mode='mirror')

    if raw_mode==0:#RGGB
        gf_img[0::2,1::2] = gf_img2[0::2,1::2]
        gf_img[1::2,0::2] = gf_img2[1::2,0::2]
    elif raw_mode==1:#GRBG
        gf_img[0::2,0::2] = gf_img2[0::2,0::2]
        gf_img[1::2,1::2] = gf_img2[1::2,1::2]
    elif raw_mode==2:#GBRG
        gf_img[0::2,0::2] = gf_img2[0::2,0::2]
        gf_img[1::2,1::2] = gf_img2[1::2,1::2]
    elif raw_mode==3:#BGGR
        gf_img[0::2,1::2] = gf_img2[0::2,1::2]
        gf_img[1::2,0::2] = gf_img2[1::2,0::2]
    else:
        gf_img = gf_img2

    return gf_img

def raw_nlm(target_img):
    return target_img

def wb_set_value(target_img,gain,raw_mode):
    out_img = np.zeros_like(target_img)
    if raw_mode==0:#RGGB
        out_img[0::2,0::2] = target_img[0::2,0::2]*gain[0]
        out_img[0::2,1::2] = target_img[0::2,1::2]*gain[1]
        out_img[1::2,0::2] = target_img[1::2,0::2]*gain[1]
        out_img[1::2,1::2] = target_img[1::2,1::2]*gain[2]
    elif raw_mode==1:#GRBG
        out_img[0::2,0::2] = target_img[0::2,0::2]*gain[1]
        out_img[0::2,1::2] = target_img[0::2,1::2]*gain[0]
        out_img[1::2,0::2] = target_img[1::2,0::2]*gain[2]
        out_img[1::2,1::2] = target_img[1::2,1::2]*gain[1]
    elif raw_mode==2:#GBRG
        out_img[0::2,0::2] = target_img[0::2,0::2]*gain[1]
        out_img[0::2,1::2] = target_img[0::2,1::2]*gain[2]
        out_img[1::2,0::2] = target_img[1::2,0::2]*gain[0]
        out_img[1::2,1::2] = target_img[1::2,1::2]*gain[1]
    elif raw_mode==3:#BGGR
        out_img[0::2,0::2] = target_img[0::2,0::2]*gain[2]
        out_img[0::2,1::2] = target_img[0::2,1::2]*gain[1]
        out_img[1::2,0::2] = target_img[1::2,0::2]*gain[1]
        out_img[1::2,1::2] = target_img[1::2,1::2]*gain[0]
    else:
        out_img[0::2,0::2] = target_img[0::2,0::2]*gain[0]
        out_img[0::2,1::2] = target_img[0::2,1::2]*gain[1]
        out_img[1::2,0::2] = target_img[1::2,0::2]*gain[1]
        out_img[1::2,1::2] = target_img[1::2,1::2]*gain[2]
    return out_img

def wb_gray_world(target_img,dummy,raw_mode):
    if raw_mode==0:#RGGB
        g_mean = np.mean(np.array([target_img[0::2,1::2],target_img[1::2,0::2]]))
        r_gain = g_mean/np.mean(target_img[0::2,0::2])
        b_gain = g_mean/np.mean(target_img[1::2,1::2])
    elif raw_mode==1:#GRBG
        g_mean = np.mean(np.array([target_img[0::2,0::2],target_img[1::2,1::2]]))
        r_gain = g_mean/np.mean(target_img[0::2,1::2])
        b_gain = g_mean/np.mean(target_img[1::2,0::2])
    elif raw_mode==2:#GBRG
        g_mean = np.mean(np.array([target_img[0::2,0::2],target_img[1::2,1::2]]))
        r_gain = g_mean/np.mean(target_img[1::2,0::2])
        b_gain = g_mean/np.mean(target_img[0::2,1::2])
    elif raw_mode==3:#BGGR
        g_mean = np.mean(np.array([target_img[0::2,1::2],target_img[1::2,0::2]]))
        r_gain = g_mean/np.mean(target_img[1::2,1::2])
        b_gain = g_mean/np.mean(target_img[0::2,0::2])
    else:
        g_mean = np.mean(np.array([target_img[0::2,1::2],target_img[1::2,0::2]]))
        r_gain = g_mean/np.mean(target_img[0::2,0::2])
        b_gain = g_mean/np.mean(target_img[1::2,1::2])
    return wb_set_value(target_img,[r_gain,1,b_gain],raw_mode=raw_mode)


def demosaic_through(target_img,dummy,raw_mode):
    return np.tile(target_img[:,:,np.newaxis],(1,1,3))

def demosaic_121(target_img,dummy,raw_mode):
    """
    Low quality demosaic.
    R and B are just interpolated with 121 filter, G with 141 filter.
    低クオリティのデモザイク。
    R,Bは121フィルタ、Gは141フィルタで補間してるだけ。
    :param target_img:  bayer
    :return:            RGB
    """
    fil_RB = np.array([[1, 2, 1],
                       [2, 4, 2],
                       [1, 2, 1]]) / 4
    fil_G = np.array([[0, 1, 0],
                      [1, 4, 1],
                      [0, 1, 0]]) / 4

    target_rawR = np.zeros_like(target_img)
    target_rawB = np.zeros_like(target_img)
    target_rawG = np.zeros_like(target_img)
    out_img = np.zeros((np.shape(target_img)[0], np.shape(target_img)[1], 3))

    if raw_mode==0:#RGGB
        target_rawR[0::2, 0::2] = target_img[0::2,0::2].copy()
        target_rawG[0::2, 1::2] = target_img[0::2,1::2].copy()
        target_rawG[1::2, 0::2] = target_img[1::2,0::2].copy()
        target_rawB[1::2, 1::2] = target_img[1::2,1::2].copy()
    elif raw_mode==1:#GRBG
        target_rawG[0::2,0::2] = target_img[0::2,0::2].copy()
        target_rawR[0::2,1::2] = target_img[0::2,1::2].copy()
        target_rawB[1::2,0::2] = target_img[1::2,0::2].copy()
        target_rawG[1::2,1::2] = target_img[1::2,1::2].copy()
    elif raw_mode==2:#GBRG
        target_rawG[0::2,0::2] = target_img[0::2,0::2].copy()
        target_rawB[0::2,1::2] = target_img[0::2,1::2].copy()
        target_rawR[1::2,0::2] = target_img[1::2,0::2].copy()
        target_rawG[1::2,1::2] = target_img[1::2,1::2].copy()
    elif raw_mode==3:#BGGR
        target_rawB[0::2,0::2] = target_img[0::2,0::2].copy()
        target_rawG[0::2,1::2] = target_img[0::2,1::2].copy()
        target_rawG[1::2,0::2] = target_img[1::2,0::2].copy()
        target_rawR[1::2,1::2] = target_img[1::2,1::2].copy()
    else:
        target_rawR[0::2,0::2] = target_img[0::2,0::2].copy()
        target_rawG[0::2,1::2] = target_img[0::2,1::2].copy()
        target_rawG[1::2,0::2] = target_img[1::2,0::2].copy()
        target_rawB[1::2,1::2] = target_img[1::2,1::2].copy()

    out_img[:, :, 0] = ndimage.convolve(target_rawR, fil_RB, mode='mirror')
    out_img[:, :, 2] = ndimage.convolve(target_rawB, fil_RB, mode='mirror')
    out_img[:, :, 1] = ndimage.convolve(target_rawG, fil_G, mode='mirror')

    return out_img

def demosaic_GBTF(target_img,raw_mode):
    return target_img

def matrix3x3_x_img3ch(target_img, input_mat, raw_mode):
    out_img = np.zeros_like(target_img)
    out_img[:,:,0] = target_img[:,:,0] * input_mat[0] + target_img[:, :, 1] * input_mat[1] + target_img[:, :, 2] * input_mat[2]
    out_img[:,:,1] = target_img[:,:,0] * input_mat[3] + target_img[:, :, 1] * input_mat[4] + target_img[:, :, 2] * input_mat[5]
    out_img[:,:,2] = target_img[:,:,0] * input_mat[6] + target_img[:, :, 1] * input_mat[7] + target_img[:, :, 2] * input_mat[8]
    return out_img

def gamma_set_value(target_img, input_mat, raw_mode):
    return np.power(np.clip(target_img-input_mat[1],0,input_mat[2])/(input_mat[2]-input_mat[1]), 1/input_mat[0])*(input_mat[4]-input_mat[3])+input_mat[3]

def ycconv_yuv(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[0.299,0.587,0.114,-0.14713,-0.28886,0.436,0.615,-0.51499,-0.10001],None)
def ycconv_BT601(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[0.299,0.587,0.114,-0.168736,-0.331264,0.5,0.5,-0.418688,-0.081312],None)
def ycconv_BT709(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[0.2126,0.7152,0.0722,-0.114572,-0.385428,0.5,0.5,-0.454153,-0.045847],None)

def rgbconv_yuv(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[1,0,1.13983,1,-0.39465,-0.58060,1,2.03211,0],None)
def rgbconv_BT601(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[1,0,1.402,1,-0.344136,-0.714136,1,1.772,0],None)
def rgbconv_BT709(target_img,dummy,raw_mode):
    return matrix3x3_x_img3ch(target_img,[1,0,1.5748,1,-0.187324,-0.468124,1,1.8556,0],None)

def ys_usm(target_img,shape_sigma_gain,raw_mode):
    gf = generate_gaussian_filter((shape_sigma_gain[0],shape_sigma_gain[1]),shape_sigma_gain[2])
    blur_img = ndimage.convolve(target_img[:,:,0],gf,mode='mirror')
    out_img = target_img.copy()
    out_img[:,:,0] = target_img[:,:,0] + (target_img[:,:,0]-blur_img)+shape_sigma_gain[3]
    return out_img

def c_gaussian(target_img,shape_sigma,raw_mode):
    out_img = target_img.copy()
    gf = generate_gaussian_filter((shape_sigma[0],shape_sigma[1]),shape_sigma[2])
    out_img[:,:,1] = ndimage.convolve(target_img[:,:,1],gf,mode='mirror')
    out_img[:,:,2] = ndimage.convolve(target_img[:,:,2],gf,mode='mirror')
    return out_img

def c_nlm(target_img):
    return target_img

def goc_set_value(target_img,goc_param,raw_mode):
    out_img = target_img.copy()
    out_img[:,:,0] = np.clip(target_img[:,:,0]*goc_param[0]+goc_param[1],goc_param[2],goc_param[3])
    out_img[:,:,1] = np.clip(target_img[:,:,1]*goc_param[4]+goc_param[5],goc_param[6],goc_param[7])
    out_img[:,:,2] = np.clip(target_img[:,:,2]*goc_param[8]+goc_param[9],goc_param[10],goc_param[11])
    return out_img

def through_img2img(target_img, dummy, raw_mode):
    return target_img

class development_module:
    def __init__(self,func,label_list,label_pos,lineedit_list,lineedit_pos):
        self.func = func
        self.label_list = label_list
        self.label_pos = label_pos
        self.lineedit_list = lineedit_list
        self.lineedit_pos = lineedit_pos
        pass

class raw_proc_window(object):
    def __init__(self):
        self.preview_img_before = None
        self.preview_img_dict = {}
        self.prev_img_key = ['first']
        pass

    def init_window(self,window):
        window.setWindowTitle('Q.Q.R.I.viewer -raw processing window-')
        self.centerWidget = QtWidgets.QWidget()
        window.setCentralWidget(self.centerWidget)
        self.layout = QtWidgets.QGridLayout()
        self.centerWidget.setLayout(self.layout)

        # raw type
        self.raw_type_box = QtWidgets.QGroupBox("RAW type")
        self.layout.addWidget(self.raw_type_box,0,0)
        self.raw_type_box_layout = QtGui.QGridLayout()
        self.raw_type_box.setLayout(self.raw_type_box_layout)

        self.raw_type_list = [QtWidgets.QRadioButton("RG\nGB"),
                              QtWidgets.QRadioButton("GR\nBG"),
                              QtWidgets.QRadioButton("GB\nRG"),
                              QtWidgets.QRadioButton("BG\nGR"),
                              QtWidgets.QRadioButton("WW\nWW"),]
        for i,rtl in enumerate(self.raw_type_list):
            self.raw_type_box_layout.addWidget(rtl,0,i)
        self.raw_type_list[0].setChecked(True)

        # # pseudo color
        # self.pseudo_color_box = QtWidgets.QGroupBox("Pseudo Color")
        # self.layout.addWidget(self.pseudo_color_box,1,0)
        # self.pseudo_color_box.setCheckable(True)
        # self.pseudo_color_box_layout = QtGui.QGridLayout()
        # self.pseudo_color_box.setLayout(self.pseudo_color_box_layout)

        # simple raw development
        self.simple_dev_box = QtWidgets.QGroupBox("Simple RAW Development")
        self.layout.addWidget(self.simple_dev_box,1,0)
        self.simple_dev_box.setCheckable(True)
        self.simple_dev_box.setChecked(False)
        self.simple_dev_box_layout = QtGui.QGridLayout()
        self.simple_dev_box.setLayout(self.simple_dev_box_layout)

        # preview
        self.preview_box = QtWidgets.QGroupBox("Preview")
        self.layout.addWidget(self.preview_box,0,1,2,2)
        self.preview_box_layout = QtGui.QGridLayout()
        self.preview_box.setLayout(self.preview_box_layout)
        self.preview_img_widget = pg.MultiPlotWidget()
        self.preview_box_layout.addWidget(self.preview_img_widget )
        self.preview_img_p = self.preview_img_widget.addPlot(row=0, col=0)
        self.preview_img_p.invertY(True)
        self.preview_img = pg.ImageItem()
        self.preview_img.setOpts(axisOrder='row-major')
        self.preview_img_p.addItem(self.preview_img)
        self.preview_img_p.setAspectLocked()
        self.preview_img_p.setMouseEnabled(x=False, y=False)


        self.module_dict = {}
        self.module_tab_dict = {}
        ############################################################################
        ## simple raw development - Optical Black Clamp
        self.obc_ui_dict = {'manual input':development_module(func=obc_clamp_set_val,
                                                                       label_list=[QtWidgets.QLabel('Please set constant number')],
                                                                       label_pos=[(0,0,1,1)],
                                                                       lineedit_list=[QtWidgets.QLineEdit('0')],
                                                                       lineedit_pos=[(0,1,1,1)]),
                            'clamp OBarea mean':development_module(func=obc_clamp_OBarea_val,
                                                                   label_list=[QtWidgets.QLabel('Please set OBarea pos'),
                                                                               QtWidgets.QLabel('y start'),
                                                                               QtWidgets.QLabel('x start'),
                                                                               QtWidgets.QLabel('y end'),
                                                                               QtWidgets.QLabel('x end')],
                                                                   label_pos=[(0,0,1,1),
                                                                              (0,1,1,1),
                                                                              (0,3,1,1),
                                                                              (0,5,1,1),
                                                                              (0,7,1,1),],
                                                                   lineedit_list=[QtWidgets.QLineEdit('0'),
                                                                                  QtWidgets.QLineEdit('0'),
                                                                                  QtWidgets.QLineEdit('0'),
                                                                                  QtWidgets.QLineEdit('0')],
                                                                   lineedit_pos=[(0,2,1,1),
                                                                                 (0,4,1,1),
                                                                                 (0,6,1,1),
                                                                                 (0,8,1,1),])
                            }
        self.obc_tab = self.init_module_tab(module_key='Optical Black Clamp',
                                            module_ui_dict=self.obc_ui_dict,
                                            module_key_pos=(0,0,1,1),
                                            module_tab_pos=(0,1,1,1))

        ## simple raw development - Defective Pixel Correction
        self.dpc_ui_dict = {'type1':development_module(func=dpc_type1,
                                                       label_list=[],
                                                       label_pos=[],
                                                       lineedit_list=[],
                                                       lineedit_pos=[]),
                            'through':development_module(func=through_img2img,
                                                         label_list=[],
                                                         label_pos=[],
                                                         lineedit_list=[],
                                                         lineedit_pos=[]),
                            }
        self.dpc_tab = self.init_module_tab(module_key='Defective Pixel Correction',
                                            module_ui_dict=self.dpc_ui_dict,
                                            module_key_pos=(1,0,1,1),
                                            module_tab_pos=(1,1,1,1))

        ## simple raw development - RAW Noise Reduction
        self.rawnr_ui_dict = {'gaussian':development_module(func=raw_gaussian,
                                                            label_list=[QtWidgets.QLabel('kernel y-size'),
                                                                        QtWidgets.QLabel('kernel x-size'),
                                                                        QtWidgets.QLabel('sigma'),],
                                                            label_pos=[(0,0,1,1),
                                                                       (0,2,1,1),
                                                                       (0,4,1,1)],
                                                            lineedit_list=[QtWidgets.QLineEdit('5'),
                                                                           QtWidgets.QLineEdit('5'),
                                                                           QtWidgets.QLineEdit('0'),],
                                                            lineedit_pos=[(0,1,1,1),
                                                                          (0,3,1,1),
                                                                          (0,5,1,1)]),
                              'through':development_module(func=through_img2img,
                                                           label_list=[],
                                                           label_pos=[],
                                                           lineedit_list=[],
                                                           lineedit_pos=[]),
                              }
        self.rawnr_tab = self.init_module_tab(module_key='RAW Noise Reduction',
                                              module_ui_dict=self.rawnr_ui_dict,
                                              module_key_pos=(2,0,1,1),
                                              module_tab_pos=(2,1,1,1))

        ## simple raw development - White Balance
        self.wb_ui_dict = {'manual input':development_module(func=wb_set_value,
                                                            label_list=[QtWidgets.QLabel('R-Gain'),
                                                                        QtWidgets.QLabel('G-Gain'),
                                                                        QtWidgets.QLabel('B-Gain')],
                                                            label_pos=[(0,0,1,1),(0,2,1,1),(0,4,1,1)],
                                                            lineedit_list=[QtWidgets.QLineEdit('1'),QtWidgets.QLineEdit('1'),QtWidgets.QLineEdit('1')],
                                                            lineedit_pos=[(0,1,1,1),(0,3,1,1),(0,5,1,1)]),
                           'autoWB gray-world':development_module(func=wb_gray_world,
                                                                  label_list=[],
                                                                  label_pos=[],
                                                                  lineedit_list=[],
                                                                  lineedit_pos=[]),
                           }
        self.wb_tab = self.init_module_tab(module_key='White Balance',
                                              module_ui_dict=self.wb_ui_dict,
                                              module_key_pos=(3,0,1,1),
                                              module_tab_pos=(3,1,1,1))

        ## simple raw development - Demosaic
        self.demosaic_ui_dict = {'demosaic-121':development_module(func=demosaic_121,
                                                                   label_list=[],
                                                                   label_pos=[],
                                                                   lineedit_list=[],
                                                                   lineedit_pos=[]),
                                 'through':development_module(func=demosaic_through,
                                                              label_list=[],
                                                              label_pos=[],
                                                              lineedit_list=[],
                                                              lineedit_pos=[]),
                                }
        self.demosaic_tab = self.init_module_tab(module_key='Demosaic',
                                                 module_ui_dict=self.demosaic_ui_dict,
                                                 module_key_pos=(4,0,1,1),
                                                 module_tab_pos=(4,1,1,1))

        ## simple raw development - color matrix
        self.cm_ui_dict = {'manual input':development_module(func=matrix3x3_x_img3ch,
                                                             label_list=[QtWidgets.QLabel("  R_out      "),
                                                                         QtWidgets.QLabel("( G_out ) = ("),
                                                                         QtWidgets.QLabel("  B_out      "),
                                                                         QtWidgets.QLabel("    R_in  "),
                                                                         QtWidgets.QLabel(") ( G_in )"),
                                                                         QtWidgets.QLabel("    B_in  "),],
                                                             label_pos=[(0,0,1,1),# QtWidgets.QLabel("R_out"),
                                                                        (1,0,1,1),# QtWidgets.QLabel("( G_out"),
                                                                        (2,0,1,1),# QtWidgets.QLabel("B_out"),
                                                                        (0,4,1,1),# QtWidgets.QLabel("R_in"),
                                                                        (1,4,1,1),# QtWidgets.QLabel("G_in )"),
                                                                        (2,4,1,1),# QtWidgets.QLabel("B_in"),
                                                                        ],
                                                             lineedit_list=[QtWidgets.QLineEdit("1"),QtWidgets.QLineEdit("0"),QtWidgets.QLineEdit("0"),
                                                                            QtWidgets.QLineEdit("0"),QtWidgets.QLineEdit("1"),QtWidgets.QLineEdit("0"),
                                                                            QtWidgets.QLineEdit("0"),QtWidgets.QLineEdit("0"),QtWidgets.QLineEdit("1"),],
                                                             lineedit_pos=[(0,1,1,1),(0,2,1,1),(0,3,1,1),
                                                                           (1,1,1,1),(1,2,1,1),(1,3,1,1),
                                                                           (2,1,1,1),(2,2,1,1),(2,3,1,1)]),
                           }
        self.cm_tab = self.init_module_tab(module_key='Color Matrix',
                                           module_ui_dict=self.cm_ui_dict,
                                           module_key_pos=(5,0,1,1),
                                           module_tab_pos=(5,1,1,1))

        ## simple raw development - Gamma
        self.gamma_ui_dict = {'manual input':development_module(func=gamma_set_value,
                                                                label_list=[QtWidgets.QLabel("Gamma value(1/??)"),
                                                                            QtWidgets.QLabel("input min"),
                                                                            QtWidgets.QLabel("input max"),
                                                                            QtWidgets.QLabel("output min"),
                                                                            QtWidgets.QLabel("output max")],
                                                                label_pos=[(0,0,1,1),
                                                                           (0,2,1,1),
                                                                           (0,4,1,1),
                                                                           (0,6,1,1),
                                                                           (0,8,1,1),],
                                                                lineedit_list=[QtWidgets.QLineEdit("2.1"),
                                                                               QtWidgets.QLineEdit("0"),
                                                                               QtWidgets.QLineEdit("16383"),
                                                                               QtWidgets.QLineEdit("0"),
                                                                               QtWidgets.QLineEdit("255")],
                                                                lineedit_pos=[(0,1,1,1),
                                                                              (0,3,1,1),
                                                                              (0,5,1,1),
                                                                              (0,7,1,1),
                                                                              (0,9,1,1)]),
                              'through':development_module(func=through_img2img,
                                                           label_list=[],
                                                           label_pos=[],
                                                           lineedit_list=[],
                                                           lineedit_pos=[]),
                              }
        self.gamma_tab = self.init_module_tab(module_key='Gamma',
                                              module_ui_dict=self.gamma_ui_dict,
                                              module_key_pos=(6,0,1,1),
                                              module_tab_pos=(6,1,1,1))

        ## simple raw development - YC conversion
        self.ycconv_ui_dict = {'YUV':development_module(func=ycconv_yuv,label_list=[],label_pos=[],lineedit_list=[],lineedit_pos=[]),
                               'BT.601':development_module(func=ycconv_BT601,label_list=[],label_pos=[],lineedit_list=[],lineedit_pos=[]),
                               'BT.709':development_module(func=ycconv_BT709,label_list=[],label_pos=[],lineedit_list=[],lineedit_pos=[]),
                               }
        self.ycconv_tab = self.init_module_tab(module_key='YC conversion',
                                               module_ui_dict=self.ycconv_ui_dict,
                                               module_key_pos=(7,0,1,1),
                                               module_tab_pos=(7,1,1,1))

        ## simple raw development - Y sharpness
        self.ys_ui_dict = {'unsharp':development_module(func=ys_usm,
                                                                label_list=[QtWidgets.QLabel("blur karnel y size"),
                                                                            QtWidgets.QLabel("blur karnel x size"),
                                                                            QtWidgets.QLabel("blur sigma"),
                                                                            QtWidgets.QLabel("sharpness gain"),],
                                                                label_pos=[(0,0,1,1),
                                                                           (0,2,1,1),
                                                                           (0,4,1,1),
                                                                           (0,6,1,1),],
                                                                lineedit_list=[QtWidgets.QLineEdit("5"),
                                                                               QtWidgets.QLineEdit("5"),
                                                                               QtWidgets.QLineEdit("0"),
                                                                               QtWidgets.QLineEdit("1"),],
                                                                lineedit_pos=[(0,1,1,1),
                                                                              (0,3,1,1),
                                                                              (0,5,1,1),
                                                                              (0,7,1,1),]),
                              'through':development_module(func=through_img2img,
                                                           label_list=[],
                                                           label_pos=[],
                                                           lineedit_list=[],
                                                           lineedit_pos=[]),
                              }
        self.ys_tab = self.init_module_tab(module_key='Y sharpness',
                                              module_ui_dict=self.ys_ui_dict,
                                              module_key_pos=(8,0,1,1),
                                              module_tab_pos=(8,1,1,1))


        ## simple raw development - C Noise Reduction
        self.cnr_ui_dict = {'gaussian':development_module(func=c_gaussian,
                                                          label_list=[QtWidgets.QLabel("karnel y size"),
                                                                      QtWidgets.QLabel("karnel x size"),
                                                                      QtWidgets.QLabel("sigma"),],
                                                          label_pos=[(0,0,1,1),
                                                                     (0,2,1,1),
                                                                     (0,4,1,1),],
                                                          lineedit_list=[QtWidgets.QLineEdit("5"),
                                                                         QtWidgets.QLineEdit("5"),
                                                                         QtWidgets.QLineEdit("0"),],
                                                          lineedit_pos=[(0,1,1,1),
                                                                        (0,3,1,1),
                                                                        (0,5,1,1),]),
                           }
        self.cnr_tab = self.init_module_tab(module_key='C Noise Reduction',
                                            module_ui_dict=self.cnr_ui_dict,
                                            module_key_pos=(9,0,1,1),
                                            module_tab_pos=(9,1,1,1))

        ## simple raw development - (for display) RGB conversion
        self.rgbconv_ui_dict = {}
        rgbconv_func_list = [rgbconv_yuv,rgbconv_BT601,rgbconv_BT709]
        for i,k in enumerate(self.ycconv_ui_dict.keys()):
            self.rgbconv_ui_dict[k] = development_module(func=rgbconv_func_list[i],label_list=[],label_pos=[],lineedit_list=[],lineedit_pos=[])

        self.rgbconv_tab = self.init_module_tab(module_key='RGB conversion',
                                                module_ui_dict=self.rgbconv_ui_dict,
                                                module_key_pos=(10,0,1,1),
                                                module_tab_pos=(10,1,1,1))

        self.module_tab_dict['YC conversion'].currentChanged.connect(lambda: self.update_other_tab(['YC conversion','RGB conversion']))
        self.module_tab_dict['RGB conversion'].currentChanged.connect(lambda: self.update_other_tab(['RGB conversion','YC conversion']))

        ## simple raw development - Gain Offset Clip
        self.goc_ui_dict = {'manual input':development_module(func=goc_set_value,
                                                              label_list=[QtWidgets.QLabel("clip( 0ch * "),
                                                                          QtWidgets.QLabel(" + "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" )"),
                                                                          QtWidgets.QLabel("clip( 1ch * "),
                                                                          QtWidgets.QLabel(" + "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" )"),
                                                                          QtWidgets.QLabel("clip( 2ch * "),
                                                                          QtWidgets.QLabel(" + "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" , "),
                                                                          QtWidgets.QLabel(" )"),],
                                                              label_pos=[(0,0,1,1),
                                                                         (0,2,1,1),
                                                                         (0,4,1,1),
                                                                         (0,6,1,1),
                                                                         (0,8,1,1),
                                                                         (1,0,1,1),
                                                                         (1,2,1,1),
                                                                         (1,4,1,1),
                                                                         (1,6,1,1),
                                                                         (1,8,1,1),
                                                                         (2,0,1,1),
                                                                         (2,2,1,1),
                                                                         (2,4,1,1),
                                                                         (2,6,1,1),
                                                                         (2,8,1,1),],
                                                              lineedit_list=[QtWidgets.QLineEdit("1"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("999999"),
                                                                             QtWidgets.QLineEdit("1"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("999999"),
                                                                             QtWidgets.QLineEdit("1"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("0"),
                                                                             QtWidgets.QLineEdit("999999"),],
                                                              lineedit_pos=[(0,1,1,1),
                                                                            (0,3,1,1),
                                                                            (0,5,1,1),
                                                                            (0,7,1,1),
                                                                            (1,1,1,1),
                                                                            (1,3,1,1),
                                                                            (1,5,1,1),
                                                                            (1,7,1,1),
                                                                            (2,1,1,1),
                                                                            (2,3,1,1),
                                                                            (2,5,1,1),
                                                                            (2,7,1,1),]),
                            }
        self.goc_tab = self.init_module_tab(module_key='Gain Offset Clip',
                                            module_ui_dict=self.goc_ui_dict,
                                            module_key_pos=(11,0,1,1),
                                            module_tab_pos=(11,1,1,1))

        ## simple raw development - run button
        self.simple_dev_run_btn = QtWidgets.QPushButton('run')
        self.layout.addWidget(self.simple_dev_run_btn,2,2)

        self.simple_dev_save_btn = QtWidgets.QPushButton('save setting')
        self.layout.addWidget(self.simple_dev_save_btn,2,0)

        self.simple_dev_load_btn = QtWidgets.QPushButton('load setting')
        self.layout.addWidget(self.simple_dev_load_btn,2,1)

        pass

    def update_other_tab(self,module_key_list):
        self.module_tab_dict[module_key_list[1]].setCurrentIndex(self.module_tab_dict[module_key_list[0]].currentIndex())
        pass


    def init_module_tab(self,module_key,module_ui_dict,module_key_pos,module_tab_pos):
        self.module_dict[module_key] = module_ui_dict
        module_tab = QtWidgets.QTabWidget() # 当該モジュールのタブ
        module_tab_list = [] # 当該モジュールの個々のタブ
        module_tab_layout_list = [] # tab内のレイアウト
        for each_func_key in module_ui_dict.keys():
            module_tab_list.append(QtWidgets.QWidget())
            module_tab.addTab(module_tab_list[-1], each_func_key)
            module_tab_layout_list.append(QtWidgets.QGridLayout())
            module_tab_list[-1].setLayout(module_tab_layout_list[-1])
            if len(module_ui_dict[each_func_key].label_list) != 0:
                for i,la in enumerate(module_ui_dict[each_func_key].label_list):
                    module_tab_layout_list[-1].addWidget(la,module_ui_dict[each_func_key].label_pos[i][0],module_ui_dict[each_func_key].label_pos[i][1],module_ui_dict[each_func_key].label_pos[i][2],module_ui_dict[each_func_key].label_pos[i][3])
                    # la.setMaximumWidth(120)
                    la.setAlignment(QtCore.Qt.AlignJustify)
            if len(module_ui_dict[each_func_key].lineedit_list) != 0:
                for i,le in enumerate(module_ui_dict[each_func_key].lineedit_list):
                    module_tab_layout_list[-1].addWidget(le,module_ui_dict[each_func_key].lineedit_pos[i][0],module_ui_dict[each_func_key].lineedit_pos[i][1],module_ui_dict[each_func_key].lineedit_pos[i][2],module_ui_dict[each_func_key].lineedit_pos[i][3])
                    le.editingFinished.connect(lambda: self.update_prev(module_key))
                    le.setValidator(QtGui.QDoubleValidator())
                    # le.setAlignment(QtCore.Qt.AlignJustify)
                    # le.setMaxLength(60)
                    # le.setMaximumWidth(60)
                    # QtWidgets.QLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding)
                    # le.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)


        temp = QtWidgets.QLabel(module_key)
        self.simple_dev_box_layout.addWidget(temp,module_key_pos[0],module_key_pos[1],module_key_pos[2],module_key_pos[3])
        temp.setStyleSheet("QLabel { color : #2B8B96; }")
        temp.setFont(QtGui.QFont("Arial Font", 10, QtGui.QFont.Bold))

        self.simple_dev_box_layout.addWidget(module_tab,module_tab_pos[0],module_tab_pos[1],module_tab_pos[2],module_tab_pos[3])
        module_tab.currentChanged.connect(lambda: self.update_prev(module_key))

        self.module_tab_dict[module_key] = module_tab
        self.prev_img_key.append(module_key)
        pass


    def set_img(self, raw_img):
        height,width = np.shape(raw_img)
        temp_img = raw_img[height//2-128:height//2+128,width//2-128:width//2+128].astype(float)
        # self.preview_img.setImage(temp_img)
        self.preview_img_dict['first'] = temp_img.copy()
        self.update_prev('first')
        pass

    def update_prev(self,module_key):
        run_flag = False
        prev_target_img = None
        for i,k in enumerate(self.module_tab_dict.keys()):
            if module_key==k:
                run_flag = True
                prev_target_img = self.preview_img_dict[self.prev_img_key[i]]
            elif module_key=='first' and not(run_flag):
                run_flag = True
                prev_target_img = self.preview_img_dict['first']

            if run_flag:
                now_tab_name = self.module_tab_dict[k].tabText(self.module_tab_dict[k].currentIndex())
                val_list = []
                for i in range(len(self.module_dict[k][now_tab_name].lineedit_list)):
                    val_list.append(float(self.module_dict[k][now_tab_name].lineedit_list[i].text()))

                prev_target_img = self.module_dict[k][now_tab_name].func(prev_target_img,val_list,0).copy()
                self.preview_img_dict[k] = prev_target_img.copy()

        # now_tab_name = self.module_tab_dict['YC conversion'].tabText(self.module_tab_dict['YC conversion'].currentIndex())
        # prev_target_img = self.rgbconv_ui_dict[now_tab_name].func(prev_target_img).copy()
        self.preview_img.setImage(prev_target_img)
        print(prev_target_img)
        pass


    def save_setting(self):
        pass
    def load_setting(self):
        pass

    def run_development(self,target_img):
        for i,k in enumerate(self.module_tab_dict.keys()):
            now_tab_name = self.module_tab_dict[k].tabText(self.module_tab_dict[k].currentIndex())
            val_list = []
            for i in range(len(self.module_dict[k][now_tab_name].lineedit_list)):
                val_list.append(float(self.module_dict[k][now_tab_name].lineedit_list[i].text()))
            target_img = self.module_dict[k][now_tab_name].func(target_img,val_list,0).copy()
        return target_img




class analyze_window(object):
    def __init__(self):
        # self.roi_hist_list = []
        pass

    def init_window(self,window):
        window.setWindowTitle('Q.Q.R.I.viewer -analyze window-')
        self.centerWidget = QtWidgets.QWidget()
        window.setCentralWidget(self.centerWidget)
        self.layout = QtWidgets.QGridLayout()
        self.centerWidget.setLayout(self.layout)

        # window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        #######################################################################
        #             histogram
        #######################################################################
        self.roi_hist_widget = pg.MultiPlotWidget()
        self.layout.addWidget(self.roi_hist_widget, 0, 0)

        #######################################################################
        #             table
        #######################################################################
        self.roi_table_widget = QtWidgets.QTableWidget()
        self.layout.addWidget(self.roi_table_widget, 0, 1)
        pass



class ImageviewWidget(QtGui.QWidget):

    def __init__(self, ImgPrfSettingWidget_pos=None):

        self.Widget_pos = None

        self.img_ch = None
        self.input_img = None

        self.img_roi = []
        self.img_roi_id = 0
        self.img_roi_bool = []
        self.img_loi_h = []
        self.img_loi_v = []
        self.img_loi_id = 0
        self.img_loi_bool = []
        self.xprf = []
        self.yprf = []
        self.input_img = None
        self.colormap_name = None
        self.roi_hist = None

        super().__init__()
        self.setAcceptDrops(True)
        self.img_is_stored = False #中に画像データ入ってるかフラグ
        self.Widget_pos = ImgPrfSettingWidget_pos

        # 全体の表示領域のlayout
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)#グリッドレイアウトをこのクラス全体に登録


        #######################################################################
        #             Image view & Profile & Thambnail Area Define
        #######################################################################
        # 画像の表示領域
        self.img_prf_widget = pg.MultiPlotWidget()
        self.layout.addWidget(self.img_prf_widget, 0, 0)#全体の上部に画像表示用MultiPlotWidget
        self.layout.setRowStretch(0, 10)

        image_prf_ratio = 12
        # outer plot
        outer_p_list = []
        outer_p_list.append(self.img_prf_widget.addPlot(row=0, col=0, rowspan=1, colspan=1))
        outer_p_list[-1].setMaximumHeight(1)
        outer_p_list[-1].setMaximumWidth(1)
        outer_p_list[-1].hideAxis('left')
        outer_p_list[-1].hideAxis('bottom')
        for x in np.arange(1, image_prf_ratio + 2):
            outer_p_list.append(self.img_prf_widget.addPlot(row=0, col=x, rowspan=1, colspan=1))
            outer_p_list[-1].setMaximumHeight(1)
            outer_p_list[-1].hideAxis('left')
            outer_p_list[-1].hideAxis('bottom')
        for y in np.arange(1, image_prf_ratio + 2):
            outer_p_list.append(self.img_prf_widget.addPlot(row=y, col=0, rowspan=1, colspan=1))
            outer_p_list[-1].setMaximumWidth(1)
            outer_p_list[-1].hideAxis('left')
            outer_p_list[-1].hideAxis('bottom')

        # img plot
        self.img_p = self.img_prf_widget.addPlot(row=1 + 1, col=1 + 0, rowspan=image_prf_ratio, colspan=image_prf_ratio)
        self.img_p.invertY(True)
        self.img = pg.ImageItem()
        self.img.setOpts(axisOrder='row-major')
        self.img_p.addItem(self.img)
        self.img_p.setAspectLocked()

        # thumbnail plot
        self.tmb_p = self.img_prf_widget.addPlot(row=1 + 0, col=1 + image_prf_ratio, rowspan=1, colspan=1)
        self.tmb_p.invertY(True)
        self.tmb_img = pg.ImageItem()
        self.tmb_img.setOpts(axisOrder='row-major')
        self.tmb_p.addItem(self.tmb_img)
        self.tmb_p.setAspectLocked()
        self.tmb_p.setMouseEnabled(x=False, y=False)  # サムネ表示のマウス操作ロック

        # thumbnail roi
        self.tmb_roi = pg.GraphItem()
        self.tmb_p.addItem(self.tmb_roi)
        self.img_p.sigRangeChanged.connect(self.update_tmbROI_by_img)  # img領域の移動、zoom操作に連動してサムネイル領域のROI形状変更

        # prf plot
        # x
        self.xprf_p = self.img_prf_widget.addPlot(row=1 + 0, col=1 + 0, rowspan=1, colspan=image_prf_ratio)
        self.xprf_p.setXLink(self.img_p)
        self.xprf_p.setMouseEnabled(x=False)

        # y
        self.yprf_p = self.img_prf_widget.addPlot(row=1 + 1, col=1 + image_prf_ratio, rowspan=image_prf_ratio, colspan=1)
        self.yprf_p.invertY(True)
        self.yprf_p.setYLink(self.img_p)
        self.yprf_p.setMouseEnabled(y=False)


        #######################################################################
        #             Setting Area(Hist & Input-number) Define
        #######################################################################
        # setting領域
        self.setting_widget = QtWidgets.QWidget()
        self.layout.addWidget(self.setting_widget, 1, 0)# setting領域を全体下部に
        self.setting_layout = QtGui.QGridLayout()
        self.setting_widget.setLayout(self.setting_layout)# グリッドレイアウトをこのsetting領域に登録
        self.layout.setRowStretch(1, 1)


        self.img_view_box = QtWidgets.QGroupBox("image view control")
        self.setting_layout.addWidget(self.img_view_box, 0, 0)
        self.img_view_box_layout = QtGui.QGridLayout()
        self.img_view_box.setLayout(self.img_view_box_layout)
        self.img_view_box.setStyleSheet("background-color: #4AD8DA;")

        # setting領域 : max,minの入力用
        view_min_label = QtWidgets.QLabel()
        view_min_label.setText("black level")
        view_min_label.setAlignment(QtCore.Qt.AlignCenter)
        self.img_view_box_layout.addWidget(view_min_label, 0, 0,1,1)
        self.view_min_text = QtWidgets.QLineEdit()
        self.img_view_box_layout.addWidget(self.view_min_text, 0, 1, 1,1)

        view_max_label = QtWidgets.QLabel()
        view_max_label.setText("white level")
        view_max_label.setAlignment(QtCore.Qt.AlignCenter)
        self.img_view_box_layout.addWidget(view_max_label, 0, 2,1,1)
        self.view_max_text = QtWidgets.QLineEdit()
        self.img_view_box_layout.addWidget(self.view_max_text, 0, 3, 1,1)

        hist_step_label = QtWidgets.QLabel()
        hist_step_label.setText("hist step")
        hist_step_label.setAlignment(QtCore.Qt.AlignCenter)
        self.img_view_box_layout.addWidget(hist_step_label, 1, 0,1,1)
        self.hist_step_text = QtWidgets.QLineEdit()
        self.img_view_box_layout.addWidget(self.hist_step_text, 1, 1, 1,1)
        self.hist_step_text.setText('10')

        # hist表示
        self.hist_widget = pg.MultiPlotWidget()
        self.setting_layout.addWidget(self.hist_widget, 0, 1, 3,100)
        self.img_hist = self.hist_widget.addPlot(0,0,2,1)
        self.img_hist.showGrid(x=True, y=True, alpha=0.8)
        self.img_hist_plot0 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),stepMode=True, fillLevel=0, pen=pg.mkPen(color=(255,10,10),width=2))
        self.img_hist_plot1 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,255,10),width=2))
        self.img_hist_plot2 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,10,255),width=2))
        self.img_hist.addItem(self.img_hist_plot0)
        self.img_hist.addItem(self.img_hist_plot1)
        self.img_hist.addItem(self.img_hist_plot2)

        # hist region
        self.hist_region = pg.LinearRegionItem(swapMode='block')
        self.hist_region.setZValue(10)
        self.img_hist.addItem(self.hist_region)
        self.hist_region.lines[0].addMarker('<|', 0.5)
        self.hist_region.lines[1].addMarker('|>', 0.5)

        # colorbar
        self.colorbar_p = self.hist_widget.addPlot(2,0,1,1)
        self.colorbar_p.setMaximumHeight(14)
        self.colorbar = pg.ImageItem()
        self.colorbar.setOpts(axisOrder='row-major')
        self.colorbar_p.addItem(self.colorbar)
        self.colorbar_p.setMouseEnabled(x=False, y=False)
        self.colorbar_p.hideAxis('left')
        self.colorbar_p.hideAxis('bottom')

        # setting領域 ： colormap
        colormap_label = QtWidgets.QLabel()
        colormap_label.setText("colormap")
        colormap_label.setAlignment(QtCore.Qt.AlignCenter)
        self.img_view_box_layout.addWidget(colormap_label, 1,2)
        self.colormap_name_list = ['gray', 'viridis', 'jet', 'spring', 'summer', 'autumn', 'winter', 'cool', 'hot', 'coolwarm',
                                   'gnuplot', 'gnuplot2', 'plasma', 'inferno', 'magma', 'cividis', 'hsv', 'ocean',
                                   'twilight', 'twilight_shifted', 'seismic', 'copper', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20']
        self.colormap_cb = QtWidgets.QComboBox()
        self.colormap_cb.addItems(self.colormap_name_list)
        self.img_view_box_layout.addWidget(self.colormap_cb, 1, 3)
        self.colormap_cb.currentIndexChanged.connect(self.set_colormap)


        # image proc
        self.img_proc_box = QtWidgets.QGroupBox("image edit")
        self.setting_layout.addWidget(self.img_proc_box, 2, 0)
        self.img_proc_box_layout = QtGui.QGridLayout()
        self.img_proc_box.setLayout(self.img_proc_box_layout)
        self.img_proc_box.setStyleSheet("background-color: #2B8B96;")

        # img_proc_label = QtWidgets.QLabel()
        # img_proc_label.setText("img proc")
        # img_proc_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.img_proc_box_layout.addWidget(img_proc_label,0,0)
        # ch_swap
        self.ch_swap_btn = QtWidgets.QPushButton("ch swap", self)
        self.img_proc_box_layout.addWidget(self.ch_swap_btn,0,0)
        # 1
        self.Under_Construction1_btn = QtWidgets.QPushButton("---", self)
        self.img_proc_box_layout.addWidget(self.Under_Construction1_btn, 0, 1)
        # 2
        self.Under_Construction2_btn = QtWidgets.QPushButton("---", self)
        self.img_proc_box_layout.addWidget(self.Under_Construction2_btn, 0, 2)
        self.init_raw_proc_window()

        # img_proc_label.setStyleSheet("color: white")
        self.ch_swap_btn.setStyleSheet("color: white")
        self.Under_Construction1_btn.setStyleSheet("color: white")
        self.Under_Construction2_btn.setStyleSheet("color: white")


        # size adj
        fm = self.view_min_text.fontMetrics()
        m = self.view_min_text.textMargins()
        c = self.view_min_text.contentsMargins()
        max_width_base = 10*fm.width('x')+m.left()+m.right()+c.left()+c.right()
        self.img_view_box.setMaximumWidth((max_width_base+8)*2+max_width_base*2+30)
        self.img_proc_box.setMaximumWidth((max_width_base+8)*2+max_width_base*2+30)
        self.img_view_box.setMaximumHeight(80)
        self.img_proc_box.setMaximumHeight(60)

        # setting領域コネクト
        self.hist_region.sigRegionChangeFinished.connect(self.update_img_level_by_region)
        self.view_min_text.editingFinished.connect(self.update_img_level_by_text)
        self.view_max_text.editingFinished.connect(self.update_img_level_by_text)
        self.hist_step_text.editingFinished.connect(self.update_hist)
        self.ch_swap_btn.clicked.connect(self.ch_swap)
        self.Under_Construction2_btn.clicked.connect(self.open_raw_proc_window)

        pass

    def init_raw_proc_window(self):
        self.raw_proc_window = QtWidgets.QMainWindow()
        self.raw_proc_window_ui = raw_proc_window()
        self.raw_proc_window_ui.init_window(self.raw_proc_window)
        self.raw_proc_window_ui.simple_dev_run_btn.clicked.connect(self.run_development)
        pass

    def run_development(self):
        self.input_img = self.raw_proc_window_ui.run_development(self.img.image)
        self.update_img()
        pass

    def open_raw_proc_window(self):
        if self.img_is_stored:
            prev_img = self.img.image
        else:
            prev_img = np.ones((256,256))*128
        self.raw_proc_window_ui.set_img(prev_img)
        self.raw_proc_window.show()
        pass

    def ch_swap(self):
        while True:
            csd = ch_swap_Dialog()
            path_0ch,path_1ch,path_2ch,img_format = csd.getdata()
            if path_0ch=='cancel':
                print('cancel')
                break
            else:
                # print('koko')
                if self.img_ch==3:
                    if not path_0ch:
                        temp_img_0ch = self.img.image[:,:,0]
                    else:
                        self.read_img(path_0ch)
                        if np.ndim(self.input_img) == 2:
                            temp_img_0ch = self.input_img
                        else:
                            print('Please enter 1ch image path')
                            break
                    if not path_1ch:
                        temp_img_1ch = self.img.image[:,:,1]
                    else:
                        self.read_img(path_1ch)
                        if np.ndim(self.input_img) == 2:
                            temp_img_1ch = self.input_img
                        else:
                            print('Please enter 1ch image path')
                            break
                    if not path_2ch:
                        temp_img_2ch = self.img.image[:,:,2]
                    else:
                        self.read_img(path_2ch)
                        if np.ndim(self.input_img) == 2:
                            temp_img_2ch = self.input_img
                        else:
                            print('Please enter 1ch image path')
                            break

                    if np.shape(temp_img_0ch)==np.shape(temp_img_1ch) and np.shape(temp_img_1ch)==np.shape(temp_img_2ch):
                        if img_format=='RGB':
                            self.input_img = np.zeros((np.shape(temp_img_0ch)[0],np.shape(temp_img_0ch)[1],3))
                            self.input_img[:,:,0] = temp_img_0ch
                            self.input_img[:,:,1] = temp_img_1ch
                            self.input_img[:,:,2] = temp_img_2ch
                        elif img_format=='YUV422(8bit)':
                            temp_img_cb = temp_img_1ch.copy()
                            temp_img_cb[:,1::2] = temp_img_1ch[:,0::2]
                            temp_img_cb = temp_img_cb - 128
                            temp_img_cr = temp_img_1ch.copy()
                            temp_img_cr[:,0::2] = temp_img_1ch[:,1::2]
                            temp_img_cr = temp_img_cr - 128
                            temp_img_r = temp_img_0ch+temp_img_cr*1.13983
                            temp_img_g = temp_img_0ch+temp_img_cb*(-0.39465)+temp_img_cr*(-0.58060)
                            temp_img_b = temp_img_0ch+temp_img_cb*2.03211
                            self.input_img = np.zeros((np.shape(temp_img_0ch)[0],np.shape(temp_img_0ch)[1],3))
                            self.input_img[:,:,0] = temp_img_r
                            self.input_img[:,:,1] = temp_img_g
                            self.input_img[:,:,2] = temp_img_b
                        elif img_format=='ITU-R_BT.601(8bit)':
                            temp_img_cb = temp_img_1ch.copy()
                            temp_img_cb[:,1::2] = temp_img_1ch[:,0::2]
                            temp_img_cb = temp_img_cb - 128
                            temp_img_cr = temp_img_1ch.copy()
                            temp_img_cr[:,0::2] = temp_img_1ch[:,1::2]
                            temp_img_cr = temp_img_cr - 128
                            temp_img_r = temp_img_0ch+temp_img_cr*1.402
                            temp_img_g = temp_img_0ch+temp_img_cb*(-0.344136)+temp_img_cr*(-0.714136)
                            temp_img_b = temp_img_0ch+temp_img_cb*1.772
                            self.input_img = np.zeros((np.shape(temp_img_0ch)[0],np.shape(temp_img_0ch)[1],3))
                            self.input_img[:,:,0] = temp_img_r
                            self.input_img[:,:,1] = temp_img_g
                            self.input_img[:,:,2] = temp_img_b
                        elif img_format=='ITU-R_BT.709(8bit)':
                            temp_img_cb = temp_img_1ch.copy()
                            temp_img_cb[:,1::2] = temp_img_1ch[:,0::2]
                            temp_img_cb = temp_img_cb - 128
                            temp_img_cr = temp_img_1ch.copy()
                            temp_img_cr[:,0::2] = temp_img_1ch[:,1::2]
                            temp_img_cr = temp_img_cr - 128
                            temp_img_r = temp_img_0ch+temp_img_cr*1.5748
                            temp_img_g = temp_img_0ch+temp_img_cb*(-0.187324)+temp_img_cr*(-0.468124)
                            temp_img_b = temp_img_0ch+temp_img_cb*1.8556
                            self.input_img = np.zeros((np.shape(temp_img_0ch)[0],np.shape(temp_img_0ch)[1],3))
                            self.input_img[:,:,0] = temp_img_r
                            self.input_img[:,:,1] = temp_img_g
                            self.input_img[:,:,2] = temp_img_b
                        #end

                        self.update_img()
                        break
                    else:
                        print('height or width is different between channels')
                        break
                else:
                    print('now image is 1ch')
                    break




    ####################################################################################################################
    #                                        Image reading by Drag&Drop
    ####################################################################################################################
    def update_hist(self):
        hist_step = float(self.hist_step_text.text())
        if self.img_ch == 3:
            y, x = np.histogram(self.img.image[:, :, 0], range=[self.img_min,self.img_max+1], bins=np.arange(self.img_min,self.img_max+hist_step+1,hist_step))
            self.img_hist_plot0.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(255,10,10),width=2))
            y, x = np.histogram(self.img.image[:, :, 1], range=[self.img_min,self.img_max+1], bins=np.arange(self.img_min,self.img_max+hist_step+1,hist_step))
            self.img_hist_plot1.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,255,10),width=2))
            y, x = np.histogram(self.img.image[:, :, 2], range=[self.img_min,self.img_max+1], bins=np.arange(self.img_min,self.img_max+hist_step+1,hist_step))
            self.img_hist_plot2.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(50,100,255),width=2))

        elif self.img_ch == 1:
            y, x = np.histogram(self.img.image, range=[self.img_min,self.img_max+1], bins=np.arange(self.img_min,self.img_max+hist_step+1,hist_step))
            self.img_hist_plot0.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))
            self.img_hist_plot1.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))
            self.img_hist_plot2.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))

        pass


    def update_img(self):
        # image 更新
        self.img.setImage(self.input_img)
        self.img.setRect(pg.QtCore.QRectF(-0.5, -0.5, np.shape(self.input_img)[1], np.shape(self.input_img)[0]))
        self.tmb_img.setImage(self.input_img)

        if np.ndim(self.img.image) == 3 and np.shape(self.img.image)[2] == 3:
            self.img_ch = 3
        elif np.ndim(self.img.image) == 2:
            self.img_ch = 1

        #
        self.img_path_str = str(self.img.image)
        self.view_max_in = np.max(self.img.image)
        self.img_max = self.view_max_in
        self.view_min_in = np.min(self.img.image)
        self.img_min = self.view_min_in
        self.img_is_stored = True

        # hist更新
        self.update_hist()
        self.set_colormap()

        self.input_img = None
        self.update_region()
        self.update_minmax_text()

        for i in np.arange(0,self.img_loi_id):
            self.add_xyprf_linking_imgLOI(i)

        pass

    def dragEnterEvent(self, event):
        event.accept()
        mimeData = event.mimeData()
        mimeList = mimeData.formats()
        self.img_path = None
        if "text/uri-list" in mimeList:
            filename = mimeData.data("text/uri-list")
            filename = str(filename, encoding="utf-8")
            filename = filename.replace("file:///", "").replace("\r\n", "").replace("%20", " ")
            self.img_path = Path(urllib.parse.unquote(filename))
        pass

    def dragMoveEvent(self, event):
        pass

    def dropEvent(self, event):
        event.accept()
        event.acceptProposedAction()
        print(self.img_path)
        ImageFile.LOAD_TRUNCATED_IMAGES = True

        self.read_img()
        self.update_img()
        pass

    def read_img(self, img_path=None):
        if img_path==None:
            img_path = str(self.img_path)
        try:
            # PILLOW can open:BMP,EPS,GIF,ICNS,IM,JPEG,JPEG 2000,MSP,PCX,PNG,PPM,SPIDER,TIFF,WebP,XBM,
            #                 CUR,DCX,DDS,FLI,FLC,FPX,FTEX,GBR,GD,ICO,IMT,IPTC/NAA,MCIDAS,MIC,MPO,PCD,PIXAR,PSD,SGI,TGA,WAL,XPM
            self.input_img = np.array(Image.open(img_path)).astype(float)
        except OSError as e:
            # unknown image
            # pop up dialog for binary data and open
            self.read_binary_img_with_dialog()
            pass

        pass

    def read_binary_img_with_dialog(self):
        while True:
            bo = Binary_img_Dialog()
            bit_width,header_bytes,height,width = bo.getdata()
            bo.destroy()
            print(bit_width,header_bytes,height,width)
            if bit_width=='cancel':
                print('cancel')
                break
            elif (len(header_bytes)==0  or len(height)==0 or len(width)==0):
                print('enter correct number')
            else:
                # bit_width = int(bit_width)
                header_bytes = int(header_bytes)
                height = int(height)
                width = int(width)
                if (bit_width<=0 or header_bytes<0 or height<=0 or width<=0):
                    print('enter correct number')
                else:
                    if bit_width==16:
                        img = np.fromfile(str(self.img_path), np.uint16)
                        self.input_img = img[header_bytes//2:].reshape([height, width]).astype(float)
                    elif bit_width==8:
                        img = np.fromfile(str(self.img_path), np.uint8)
                        self.input_img = img[header_bytes:].reshape([height, width]).astype(float)
                    elif bit_width==32:
                        img = np.fromfile(str(self.img_path), np.uint32)
                        self.input_img = img[header_bytes//4:].reshape([height, width]).astype(float)
                break
        pass


    ####################################################################################################################
    #                                     Thamnail image's ROI realtime-update
    ####################################################################################################################
    def update_tmbROI_by_img(self):
        pos = np.array([[self.img_p.viewRange()[0][0], self.img_p.viewRange()[1][0]],
                        [self.img_p.viewRange()[0][1], self.img_p.viewRange()[1][0]],
                        [self.img_p.viewRange()[0][0], self.img_p.viewRange()[1][1]],
                        [self.img_p.viewRange()[0][1], self.img_p.viewRange()[1][1]]])
        adj = np.array([[0, 1], [1, 3], [3, 2], [2, 0]])
        self.tmb_roi.setData(pos=pos, adj=adj,
                             pen=pg.mkPen('r', width=3, style=QtCore.Qt.SolidLine),
                             size=0, pxMode=False)
        pass

    ####################################################################################################################
    #                                     Level correction
    ####################################################################################################################
    def isnum(self,str):
        try:
            float(str)
        except ValueError:
            return False
        else:
            return True

    def update_img_level(self):
        if np.ndim(self.img.image)==3:
            self.img.setLevels([[self.view_min_in, self.view_max_in],
                                [self.view_min_in, self.view_max_in],
                                [self.view_min_in, self.view_max_in]])
        elif np.ndim(self.img.image)==2:
            self.img.setLevels([self.view_min_in, self.view_max_in])
        pass

    def update_img_level_by_text(self):
        self.view_min_in = self.view_min_text.text()
        if self.isnum(self.view_min_in):
            self.view_min_in = float(self.view_min_in)

        self.view_max_in = self.view_max_text.text()
        if self.isnum(self.view_max_in):
            self.view_max_in = float(self.view_max_in)
        if self.view_max_in - self.view_min_in > 0:
            self.update_img_level()
            self.update_region()
        pass

    def update_region(self):
        self.hist_region.setRegion([self.view_min_in, self.view_max_in])
        pass


    def update_img_level_by_region(self):
        self.hist_region.setZValue(10)
        self.view_min_in, self.view_max_in = self.hist_region.getRegion()
        self.update_img_level()
        self.update_minmax_text()
        pass

    def update_minmax_text(self):
        self.view_min_text.setText(str(self.view_min_in))
        self.view_max_text.setText(str(self.view_max_in))
        pass


    ####################################################################################################################
    #                       Region of Interest(ROI)
    ####################################################################################################################
    def add_imgROI(self):
        cm = get_cmap('tab10')
        roi_color = (np.array(cm(self.img_roi_id))*255).astype(np.uint8)
        roi_color = pg.mkColor(roi_color[0],roi_color[1],roi_color[2])
        view_range = self.img_p.viewRange()
        temp_view_range_xq = (view_range[0][1]-view_range[0][0])/4
        temp_view_range_yq = (view_range[1][1]-view_range[1][0])/4
        roi_pos = (int((view_range[0][1]+view_range[0][0])/2-temp_view_range_xq),
                   int((view_range[1][1]+view_range[1][0])/2-temp_view_range_yq))
        roi_size = (int(temp_view_range_xq*2), int(temp_view_range_yq*2))
        self.img_roi.append(RectROI_ID(pos=roi_pos,
                                       size=roi_size,
                                       widget_pos=self.Widget_pos,
                                       id=self.img_roi_id,
                                       pen=pg.mkPen(roi_color),
                                       roi_color=roi_color))
        self.img_roi_bool.append(True)
        self.img_p.addItem(self.img_roi[-1])
        self.img_roi_id = self.img_roi_id + 1
        pass

    def add_imgROI_dummy(self):
        self.img_roi.append(None)
        pass

    def del_imgROI(self, imgroi_id):
        self.img_p.removeItem(self.img_roi[imgroi_id])
        self.img_roi[imgroi_id] = None
        self.img_roi_bool[imgroi_id] = False
        pass

    ####################################################################################################################
    #                       Line of Interest(LOI)
    ####################################################################################################################
    def add_imgLOI(self):
        view_range = self.img_p.viewRange()
        loi_pos_x = (view_range[0][1]+view_range[0][0])/2
        loi_pos_y = (view_range[1][1]+view_range[1][0])/2
        cm = get_cmap('tab10')
        loi_color = (np.array(cm(self.img_loi_id))*255).astype(np.uint8)
        loi_color = pg.mkColor(loi_color[0],loi_color[1],loi_color[2])
        self.img_loi_h.append(InfiniteLine_ID(pos=loi_pos_y,
                                              angle=0,
                                              movable=True,
                                              pen=pg.mkPen(loi_color, width=5),
                                              widget_pos=self.Widget_pos,
                                              id=self.img_loi_id))
        self.img_loi_v.append(InfiniteLine_ID(pos=loi_pos_x,
                                              angle=90,
                                              movable=True,
                                              pen=pg.mkPen(loi_color, width=5),
                                              widget_pos=self.Widget_pos,
                                              id=self.img_loi_id))
        self.img_loi_bool.append(True)
        self.img_p.addItem(self.img_loi_h[-1])
        self.img_p.addItem(self.img_loi_v[-1])
        self.img_loi_h[-1].sigPositionChanged.connect(self.prf_update)
        self.img_loi_v[-1].sigPositionChanged.connect(self.prf_update)

        self.add_xyprf_linking_imgLOI(self.img_loi_id)
        self.img_loi_id = self.img_loi_id + 1
        pass

    def add_xyprf_linking_imgLOI(self, loi_id):
        if self.img_is_stored:
            cm = get_cmap('tab10')
            loi_color = (np.array(cm(loi_id))*255).astype(np.uint8)
            loi_color = pg.mkColor(loi_color[0],loi_color[1],loi_color[2])

            self.xprf.append([])
            self.xprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('r')))
            self.xprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('g')))
            self.xprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('b')))
            self.xprf_p.addItem(self.xprf[-1][0])
            self.xprf_p.addItem(self.xprf[-1][1])
            self.xprf_p.addItem(self.xprf[-1][2])
            self.yprf.append([])
            self.yprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('r')))
            self.yprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('g')))
            self.yprf[-1].append(pg.PlotDataItem(pen=loi_color,symbol='o', symbolSize=5, symbolBrush=('b')))
            self.yprf_p.addItem(self.yprf[-1][0])
            self.yprf_p.addItem(self.yprf[-1][1])
            self.yprf_p.addItem(self.yprf[-1][2])
            self.xprf_update(loi_id)
            self.yprf_update(loi_id)
        pass


    def prf_update(self,event):
        if self.img_is_stored:
            if event.angle==0: # horizontal line = x-prf
                self.xprf_update(event.ID)
            elif event.angle==90: # vertical line = y-prf
                self.yprf_update(event.ID)
        pass

    def xprf_update(self,loi_id):
        y_pos = np.round(np.array(self.img_loi_h[loi_id].pos())).astype(int)[1]
        if 0<=y_pos and y_pos<np.shape(self.img.image)[0]:
            if self.img_ch == 3:
                self.xprf[loi_id][0].setData(np.squeeze(self.img.image[y_pos,:,0]))
                self.xprf[loi_id][1].setData(np.squeeze(self.img.image[y_pos,:,1]))
                self.xprf[loi_id][2].setData(np.squeeze(self.img.image[y_pos,:,2]))
            elif self.img_ch == 1:
                self.xprf[loi_id][0].setData(np.squeeze(self.img.image[y_pos,:]))
                self.xprf[loi_id][1].setData(np.squeeze(self.img.image[y_pos,:]))
                self.xprf[loi_id][2].setData(np.squeeze(self.img.image[y_pos,:]))
        else:
            if self.img_ch == 3:
                self.xprf[loi_id][0].setData(np.squeeze(np.zeros_like(self.img.image[0,:,0])))
                self.xprf[loi_id][1].setData(np.squeeze(np.zeros_like(self.img.image[0,:,0])))
                self.xprf[loi_id][2].setData(np.squeeze(np.zeros_like(self.img.image[0,:,0])))
            elif self.img_ch == 1:
                self.xprf[loi_id][0].setData(np.squeeze(np.zeros_like(self.img.image[0,:])))
                self.xprf[loi_id][1].setData(np.squeeze(np.zeros_like(self.img.image[0,:])))
                self.xprf[loi_id][2].setData(np.squeeze(np.zeros_like(self.img.image[0,:])))
        pass

    def yprf_update(self,loi_id):
        x_pos = np.round(np.array(self.img_loi_v[loi_id].pos())).astype(int)[0]
        if 0<=x_pos and x_pos<np.shape(self.img.image)[1]:
            if self.img_ch == 3:
                self.yprf[loi_id][0].setData(np.squeeze(self.img.image[:,x_pos,0]), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][1].setData(np.squeeze(self.img.image[:,x_pos,1]), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][2].setData(np.squeeze(self.img.image[:,x_pos,2]), np.arange(0,np.shape(self.img.image)[0]))
            elif self.img_ch == 1:
                self.yprf[loi_id][0].setData(np.squeeze(self.img.image[:,x_pos]), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][1].setData(np.squeeze(self.img.image[:,x_pos]), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][2].setData(np.squeeze(self.img.image[:,x_pos]), np.arange(0,np.shape(self.img.image)[0]))
        else:
            if self.img_ch == 3:
                self.yprf[loi_id][0].setData(np.squeeze(np.zeros_like(self.img.image[:,0,0])), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][1].setData(np.squeeze(np.zeros_like(self.img.image[:,0,0])), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][2].setData(np.squeeze(np.zeros_like(self.img.image[:,0,0])), np.arange(0,np.shape(self.img.image)[0]))
            elif self.img_ch == 1:
                self.yprf[loi_id][0].setData(np.squeeze(np.zeros_like(self.img.image[:,0])), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][1].setData(np.squeeze(np.zeros_like(self.img.image[:,0])), np.arange(0,np.shape(self.img.image)[0]))
                self.yprf[loi_id][2].setData(np.squeeze(np.zeros_like(self.img.image[:,0])), np.arange(0,np.shape(self.img.image)[0]))
        pass

    ####################################################################################################################
    #                       set colormap
    ####################################################################################################################
    def set_colormap(self):
        if self.img_ch == 1:
            colormap_N=256
            cm = get_cmap(self.colormap_cb.currentText(),colormap_N)
            self.colormap_lut = (np.array([cm(i) for i in range(colormap_N)]) * 255)
            self.img.setLookupTable(self.colormap_lut)
            self.colorbar.setImage(np.tile(self.colormap_lut[:,0:3],[50,1,1]).astype(np.uint8))

        elif self.img_ch == 3:
            self.colorbar.setImage(np.zeros((256,1)).astype(np.uint8))

        pass



#######################################################################################################################
#######################################################################################################################
#                                            Q.Q.R.I. viewer's window
#######################################################################################################################
#######################################################################################################################
class QqriWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.img_plot_list = []
        # self.input_img = None
        self.imgprfwidget_xnum = 0
        self.imgprfwidget_ynum = 0
        # self.whole_img_data = None
        self.img_path_list = []
        self.ref_menu_list = []
        self.img_view_state = 'normal'
        self.input_img_list = []

        self.setWindowTitle('Q.Q.R.I.viewer Ver0.5')
        self.setAcceptDrops(True)
        self.init_layout()
        self.init_menu()
        self.init_statusBar()
        self.init_analyze_window()
        self.show()

    def init_layout(self):
        #
        self.centerWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centerWidget)
        self.layout = QtWidgets.QGridLayout()
        self.centerWidget.setLayout(self.layout)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)

        #######################################################################
        #                   first ImgPrfSettingWidget define
        #######################################################################
        # first img area
        self.imgprfwidget_xnum = 0 #このwidget自体のx座標（これは最初のIPSWなので[y,x]=[0,0]）
        self.imgprfwidget_ynum = 0 #このwidget自体のy座標（これは最初のIPSWなので[y,x]=[0,0]）
        self.img_plot_list.append([ImageviewWidget(ImgPrfSettingWidget_pos=[self.imgprfwidget_ynum,
                                                                            self.imgprfwidget_xnum])])
        self.img_path_list.append([""]) #画像のパスを格納するためのリスト、何も入っていないので空
        self.layout.addWidget(self.img_plot_list[self.imgprfwidget_ynum][self.imgprfwidget_xnum],  #
                              self.imgprfwidget_ynum, self.imgprfwidget_xnum)                     #

        self.img_plot_list[0][0].img_p.scene().sigMouseMoved.connect(self.update_statusbar)

        pass

    ####################################################################################################################
    #                                     Menu bar init
    ####################################################################################################################
    def init_menu(self):
        #menubar create
        self.menubar = self.menuBar()

        # File
        self.fileMenu = self.menubar.addMenu('&File')
        ## File-exit
        self.exitAction = QtWidgets.QAction('&exit')
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(QtWidgets.qApp.quit)
        self.fileMenu.addAction(self.exitAction)


        # View
        self.ViewMenu = self.menubar.addMenu('&View')
        ## View-ImgAreaR
        self.addimgRAction = QtWidgets.QAction('&Add Image View <Horizontal>')
        self.addimgRAction.setShortcut('h')
        self.addimgRAction.triggered.connect(self.add_ImgPrfSettingWidget_R)
        self.ViewMenu.addAction(self.addimgRAction)
        ## View-ImgAreaB
        self.addimgBAction = QtWidgets.QAction('&Add Image View <Vertical>')
        self.addimgBAction.setShortcut('v')
        self.addimgBAction.triggered.connect(self.add_ImgPrfSettingWidget_B)
        self.ViewMenu.addAction(self.addimgBAction)
        ## View-delIMGarea
        self.delimgLAction = QtWidgets.QAction('&Erase Image View <Side>')
        self.delimgLAction.setShortcut('shift+h')
        self.delimgLAction.triggered.connect(self.del_ImgPrfSettingWidget_L)
        self.ViewMenu.addAction(self.delimgLAction)
        ## View-delIMGarea
        self.delimgUAction = QtWidgets.QAction('&Erase Image View <Down>')
        self.delimgUAction.setShortcut('shift+v')
        self.delimgUAction.triggered.connect(self.del_ImgPrfSettingWidget_U)
        self.ViewMenu.addAction(self.delimgUAction)

        # Analyze
        self.AnalyzeMenu = self.menubar.addMenu('&Analyze')
        ## Analyze-Refarence Image Select Menu
        self.refimg_select_Menu = self.AnalyzeMenu.addMenu('&Refarence Image Select')
        ### Analyze-Refarence Image Select Menu-IMG number add
        self.ref_menu_list.append(QtWidgets.QAction(str(0), self))
        self.refimg_select_Menu.addAction(self.ref_menu_list[-1])

        ## Analyze-Add ROI
        self.add_roi_Action = QtWidgets.QAction('&Add Region of Interest')
        self.add_roi_Action.setShortcut('r')
        self.add_roi_Action.triggered.connect(self.add_imgROI)
        self.AnalyzeMenu.addAction(self.add_roi_Action)

        ## Analyze-Add LOI
        self.add_loi_Action = QtWidgets.QAction('&Add Line of Interest')
        self.add_loi_Action.setShortcut('t')
        self.add_loi_Action.triggered.connect(self.add_imgLOI)
        self.AnalyzeMenu.addAction(self.add_loi_Action)

        ## Analyze-open Analyze window
        self.open_aw_Action = QtWidgets.QAction('&Open Analyze Window')
        self.open_aw_Action.setShortcut('Ctrl+@')
        self.open_aw_Action.triggered.connect(self.open_analyze_window)
        self.AnalyzeMenu.addAction(self.open_aw_Action)

        pass



    ####################################################################################################################
    #                                   statusBar
    ####################################################################################################################
    def init_statusBar(self):
        self.statusBar = self.statusBar()

    def update_statusbar(self,pos):
        img_pos = self.img_plot_list[0][0].img_p.vb.mapSceneToView(pos)
        img_pos_x = int(img_pos.x()+0.5)
        img_pos_y = int(img_pos.y()+0.5)

        statusbar_str = str((img_pos_x,img_pos_y))
        i = 0
        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                if (self.img_plot_list[y][x].img_is_stored):
                    img_size = np.shape(self.img_plot_list[y][x].img.image)
                    if -1<img_pos_y and img_pos_y<img_size[0] and -1<img_pos_x and img_pos_x<img_size[1]:
                        if np.ndim(self.img_plot_list[y][x].img.image)>2:
                            statusbar_str = statusbar_str + ' Img' + str(i) + ' : ' + str(self.img_plot_list[y][x].img.image[img_pos_y, img_pos_x, :])
                        else:
                            statusbar_str = statusbar_str + ' Img' + str(i) + ' : ' + str(self.img_plot_list[y][x].img.image[img_pos_y, img_pos_x])
                i = i + 1
        self.statusBar.showMessage(statusbar_str)
        pass

    ####################################################################################################################
    #                                   analyze window
    ####################################################################################################################
    def init_analyze_window(self):
        self.analyze_window = QtWidgets.QMainWindow()
        self.analyze_window_ui = analyze_window()
        self.analyze_window_ui.init_window(self.analyze_window)
        self.img_plot_list[0][0].roi_hist = self.analyze_window_ui.roi_hist_widget.addPlot(0, 0)

        self.analyze_window_ui.roi_table_widget.setColumnCount(2)
        self.update_row_analyze_table()
        pass

    def open_analyze_window(self):
        self.analyze_window.show()
        pass

    def update_row_analyze_table(self):
        self.analyze_window_ui.roi_table_widget.setRowCount((self.imgprfwidget_ynum + 1)
                                                            * (self.imgprfwidget_xnum + 1)
                                                            * len(RectROI_ID.roi_stats_func.keys()))
        for i in np.arange((self.imgprfwidget_ynum + 1) * (self.imgprfwidget_xnum + 1)):
            self.analyze_window_ui.roi_table_widget.setItem(i*len(RectROI_ID.roi_stats_func.keys()),0,QtWidgets.QTableWidgetItem('img'+str(i)))
            for j,k in enumerate(RectROI_ID.roi_stats_func.keys()):
                self.analyze_window_ui.roi_table_widget.setItem(i*len(RectROI_ID.roi_stats_func.keys())+j,1,QtWidgets.QTableWidgetItem(k))
        pass

    def add_col_analyze_table(self):
        self.analyze_window_ui.roi_table_widget.setColumnCount(2+len(self.img_plot_list[0][0].img_roi)*3)
        temp_header = ['img_number', 'stats']
        for i in np.arange(len(self.img_plot_list[0][0].img_roi)):
            temp_header.append('roi'+str(i)+'_0ch')
            temp_header.append('roi'+str(i)+'_1ch')
            temp_header.append('roi'+str(i)+'_2ch')
        self.analyze_window_ui.roi_table_widget.setHorizontalHeaderLabels(temp_header)
        pass


    ####################################################################################################################
    #                                   imgROI Add & update & Align ROI to A
    ####################################################################################################################
    def add_imgROI(self):
        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                self.img_plot_list[y][x].add_imgROI()
                self.img_plot_list[y][x].img_roi[-1].sigRegionChangeFinished.connect(self.update_imgROI)
                self.img_plot_list[y][x].img_roi[-1].sigRemoveRequested.connect(self.del_imgROI)
                self.img_plot_list[y][x].roi_hist.addItem(self.img_plot_list[y][x].img_roi[-1].roi_hist_plot0) # analyze windowのplotItemに RectROI_IDのPlotDataItemをadd
                self.img_plot_list[y][x].roi_hist.addItem(self.img_plot_list[y][x].img_roi[-1].roi_hist_plot1) # analyze windowのplotItemに RectROI_IDのPlotDataItemをadd
                self.img_plot_list[y][x].roi_hist.addItem(self.img_plot_list[y][x].img_roi[-1].roi_hist_plot2) # analyze windowのplotItemに RectROI_IDのPlotDataItemをadd
        self.add_col_analyze_table()
        pass

    def del_imgROI(self,event):
        imgroi_id = event.ID
        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                self.img_plot_list[y][x].roi_hist.removeItem(self.img_plot_list[y][x].img_roi[imgroi_id].roi_hist_plot0) # analyze windowのplotItemから RectROI_IDのPlotDataItemを削除
                self.img_plot_list[y][x].roi_hist.removeItem(self.img_plot_list[y][x].img_roi[imgroi_id].roi_hist_plot1) # analyze windowのplotItemから RectROI_IDのPlotDataItemを削除
                self.img_plot_list[y][x].roi_hist.removeItem(self.img_plot_list[y][x].img_roi[imgroi_id].roi_hist_plot2) # analyze windowのplotItemから RectROI_IDのPlotDataItemを削除
                self.img_plot_list[y][x].del_imgROI(imgroi_id)
        pass


    def update_imgROI(self, event):
        """
        各imgROIを連動させる
        :param event:
        :return:
        """
        id = event.get_ID_widgetpos()[1]
        pos = event.pos()
        pos = (np.round(pos[0]+0.5)-0.5, np.round(pos[1]+0.5)-0.5)
        size = event.size()
        size = (np.floor(size[0]), np.floor(size[1]))

        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                # ROI位置調整
                self.img_plot_list[y][x].img_roi[id].setPos(pos=pos,  finish=False)
                self.img_plot_list[y][x].img_roi[id].setSize(size=size,  finish=False)

                if self.img_plot_list[y][x].img_is_stored:# 画像がある場合
                    img_size = np.shape(self.img_plot_list[y][x].img.image)
                    pos_s = (np.clip((np.round(pos[0]+0.5)).astype(int),0, img_size[1]), np.clip((np.round(pos[1]+0.5)).astype(int),0, img_size[0]))
                    pos_e = (np.clip(pos_s[0]+size[0], 0, img_size[1]).astype(int), np.clip(pos_s[1]+size[1], 0, img_size[0]).astype(int))
                    self.img_plot_list[y][x].img_roi[id].roi_pos  = [[pos_s[1], pos_e[1]], [pos_s[0], pos_e[0]]]
                    self.img_plot_list[y][x].img_roi[id].roi_size = [pos_e[1]-pos_s[1], pos_e[0]-pos_s[0]]
                    self.img_plot_list[y][x].img_roi[id].roi_pix  = self.img_plot_list[y][x].img_roi[id].roi_size[0]*self.img_plot_list[y][x].img_roi[id].roi_size[1]
                    table_y_start = int(y*(self.imgprfwidget_xnum+1)+x)*len(self.img_plot_list[y][x].img_roi[id].roi_stats_func.keys())
                    table_x_start = int(2+id*3)
                    if self.img_plot_list[y][x].img.channels() == 3: # 3ch
                        # 統計量
                        for i,k in enumerate(self.img_plot_list[y][x].img_roi[id].roi_stats_func.keys()):
                            temp_stats = self.img_plot_list[y][x].img_roi[id].roi_stats_func[k](self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], :], axis=(0,1))
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start,
                                                                            QtWidgets.QTableWidgetItem(str(temp_stats[0])),
                                                                            )
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start+1,
                                                                            QtWidgets.QTableWidgetItem(str(temp_stats[1])),
                                                                            )
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start+2,
                                                                            QtWidgets.QTableWidgetItem(str(temp_stats[2])),
                                                                            )
                        #-end
                        # hist-0ch
                        max_0 = np.max(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 0])
                        min_0 = np.min(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 0])
                        hist_y, hist_x = np.histogram(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 0], bins=np.arange(min_0,max_0+2))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot0.setData(hist_x, hist_y, pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2), fillLevel=0, brush=(255,10,10,128))
                        # hist-1ch
                        max_1 = np.max(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 1])
                        min_1 = np.min(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 1])
                        hist_y, hist_x = np.histogram(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 1], bins=np.arange(min_1,max_1+2))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot1.setData(hist_x, hist_y, pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2), fillLevel=0, brush=(10,255,10,128))
                        # hist-2ch
                        max_2 = np.max(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 2])
                        min_2 = np.min(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 2])
                        hist_y, hist_x = np.histogram(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0], 2], bins=np.arange(min_2,max_2+2))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot2.setData(hist_x, hist_y, pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2), fillLevel=0, brush=(10,10,255,128))
                    elif self.img_plot_list[y][x].img.channels() == 1: # 1ch
                        # 統計量
                        for i,k in enumerate(self.img_plot_list[y][x].img_roi[id].roi_stats_func.keys()):
                            temp_stats = self.img_plot_list[y][x].img_roi[id].roi_stats_func[k](self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0]])
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start,
                                                                            QtWidgets.QTableWidgetItem(str(temp_stats)),
                                                                            )
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start+1,
                                                                            QtWidgets.QTableWidgetItem(""),
                                                                            )
                            self.analyze_window_ui.roi_table_widget.setItem(table_y_start+i,
                                                                            table_x_start+2,
                                                                            QtWidgets.QTableWidgetItem(""),
                                                                            )
                        # hist-0ch,1ch,2ch
                        max_0 = np.max(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0]])
                        min_0 = np.min(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0]])
                        hist_y, hist_x = np.histogram(self.img_plot_list[y][x].img.image[pos_s[1]:pos_e[1],pos_s[0]:pos_e[0]], bins=np.arange(min_0,max_0+2))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot0.setData(hist_x,hist_y,pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2),fillLevel=0, brush=(160,160,160,128))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot1.setData(hist_x,hist_y,pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2),fillLevel=0, brush=(160,160,160,128))
                        self.img_plot_list[y][x].img_roi[id].roi_hist_plot2.setData(hist_x,hist_y,pen=pg.mkPen(self.img_plot_list[y][x].img_roi[id].roi_color, width=2),fillLevel=0, brush=(160,160,160,128))

                else:# 画像が入ってない場合
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot0.setData(np.array([0,1]), np.array([0]))
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot1.setData(np.array([0,1]), np.array([0]))
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot2.setData(np.array([0,1]), np.array([0]))
        pass

    def add_imgROI_newImgPrfSettingWidget(self,new_y,new_x):
        """
        imgROIが既にある状態で、ImgPrfSettingWidgetが追加された場合に
        新規ImgPrfSettingWidgetに従来のimgROIを追加する
        :param new_y:
        :param new_x:
        :return:
        """
        for i in np.arange(0, self.img_plot_list[0][0].img_roi_id):

            if self.img_plot_list[0][0].img_roi_bool[i]:
                self.img_plot_list[new_y][new_x].add_imgROI()
                self.img_plot_list[new_y][new_x].img_roi[-1].sigRegionChangeFinished.connect(self.update_imgROI)
                pos = self.img_plot_list[0][0].img_roi[i].pos()
                size = self.img_plot_list[0][0].img_roi[i].size()
                self.img_plot_list[new_y][new_x].img_roi[i].setPos(pos=pos,  finish=False)
                self.img_plot_list[new_y][new_x].img_roi[i].setSize(size=size,  finish=False)
                # self.img_plot_list[new_y][new_x].roi_hist = self.analyze_window_ui.roi_hist_widget.addPlot(new_y,new_x)
                self.img_plot_list[new_y][new_x].roi_hist.addItem(self.img_plot_list[new_y][new_x].img_roi[i].roi_hist_plot0)
                self.img_plot_list[new_y][new_x].roi_hist.addItem(self.img_plot_list[new_y][new_x].img_roi[i].roi_hist_plot1)
                self.img_plot_list[new_y][new_x].roi_hist.addItem(self.img_plot_list[new_y][new_x].img_roi[i].roi_hist_plot2)
            else:
                self.img_plot_list[new_y][new_x].add_imgROI_dummy()
        pass

    ####################################################################################################################
    #                                   imgLOI Add & update(link other LOIs) & Align LOI to A
    ####################################################################################################################
    def add_imgLOI(self):
        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                self.img_plot_list[y][x].add_imgLOI()
                self.img_plot_list[y][x].img_loi_h[-1].sigDragged.connect(self.update_imgLOI)
                self.img_plot_list[y][x].img_loi_v[-1].sigDragged.connect(self.update_imgLOI)
        pass

    def update_imgLOI(self, event):
        """
        各imgLOIを連動させる
        :param event:
        :return:
        """
        id = event.get_ID_widgetpos()[1]
        pos = event.pos()
        angle = event.angle

        if angle==0:
            for y in np.arange(0,self.imgprfwidget_ynum+1):
                for x in np.arange(0,self.imgprfwidget_xnum+1):
                    self.img_plot_list[y][x].img_loi_h[id].setPos(pos=pos[1])
        elif angle==90:
            for y in np.arange(0,self.imgprfwidget_ynum+1):
                for x in np.arange(0,self.imgprfwidget_xnum+1):
                    self.img_plot_list[y][x].img_loi_v[id].setPos(pos=pos[0])
        pass

    def add_imgLOI_newImgPrfSettingWidget(self,new_y,new_x):
        """
        imgLOIが既にある状態で、ImgPrfSettingWidgetが追加された場合に
        新規ImgPrfSettingWidgetに従来のimgLOIを追加する
        :param new_y:
        :param new_x:
        :return:
        """
        for i in np.arange(0, self.img_plot_list[0][0].img_loi_id):
            if self.img_plot_list[0][0].img_loi_bool[i]:
                self.img_plot_list[new_y][new_x].add_imgLOI()
                self.img_plot_list[new_y][new_x].img_loi_h[-1].sigDragged.connect(self.update_imgLOI)
                self.img_plot_list[new_y][new_x].img_loi_v[-1].sigDragged.connect(self.update_imgLOI)
                pos = self.img_plot_list[0][0].img_loi_h[i].pos()[1]
                self.img_plot_list[new_y][new_x].img_loi_h[i].setPos(pos=pos)
                pos = self.img_plot_list[0][0].img_loi_h[i].pos()[0]
                self.img_plot_list[new_y][new_x].img_loi_v[i].setPos(pos=pos)
        pass



    ####################################################################################################################
    #                                     Add ImgPrfSettingWidget Right or Bottom
    ####################################################################################################################
    def add_ImgPrfSettingWidget(self,y,x):
        self.img_plot_list[y].append(ImageviewWidget(ImgPrfSettingWidget_pos=[y, x]))
        self.img_path_list[y].append("")
        self.layout.addWidget(self.img_plot_list[y][x], y, x)
        self.img_plot_list[y][x].img_p.setXLink(self.img_plot_list[0][0].img_p)
        self.img_plot_list[y][x].img_p.setYLink(self.img_plot_list[0][0].img_p)
        self.img_plot_list[y][x].roi_hist = self.analyze_window_ui.roi_hist_widget.addPlot(y,x) # analyze windowのhistplotエリア(MultiPlotWidget)にplotIttem追加

        self.add_imgROI_newImgPrfSettingWidget(y, x)
        self.add_imgLOI_newImgPrfSettingWidget(y, x)
        self.img_plot_list[y][x].img_p.scene().sigMouseMoved.connect(self.update_statusbar)

        self.update_row_analyze_table()
        pass

    def add_ImgPrfSettingWidget_B(self):
        self.img_plot_list.append([])
        self.img_path_list.append([])
        self.imgprfwidget_ynum = self.imgprfwidget_ynum + 1
        for i in np.arange(0,self.imgprfwidget_xnum+1):
            self.add_ImgPrfSettingWidget(self.imgprfwidget_ynum, i)
        self.update_ref_img_menu()
        pass

    def add_ImgPrfSettingWidget_R(self):
        self.imgprfwidget_xnum = self.imgprfwidget_xnum + 1
        for i in np.arange(0,self.imgprfwidget_ynum+1):
            self.add_ImgPrfSettingWidget(i, self.imgprfwidget_xnum)
        self.update_ref_img_menu()
        pass


    def update_ref_img_menu(self):
        # Refarence Image Select のリフレッシュ
        self.refimg_select_Menu.clear()
        self.ref_menu_list = []

        # ラジオボタンにするためにグループ登録＆排他化
        self.ref_img_radio = QtWidgets.QActionGroup(self)
        self.ref_img_radio.setExclusive(True)

        # Refarence Image Select の数字追加
        i = 0
        for y in np.arange(0,self.imgprfwidget_ynum+1):
            for x in np.arange(0,self.imgprfwidget_xnum+1):
                ### IMG number add
                self.ref_menu_list.append(QtWidgets.QAction(str(i), self, checkable=True))
                if i==0:
                    self.ref_menu_list[-1].setChecked(True) # チェックボタンの初期状態
                else:
                    self.ref_menu_list[-1].setChecked(False)  # チェックボタンの初期状態
                self.refimg_select_Menu.addAction(self.ref_menu_list[-1]) #
                self.ref_img_radio.addAction(self.ref_menu_list[-1]) #
                i = i+1
        pass


    def del_ImgPrfSettingWidget(self,y,x):
        self.layout.removeWidget(self.img_plot_list[y][x])
        self.analyze_window_ui.roi_hist_widget.removeItem(self.img_plot_list[y][x].roi_hist)
        self.img_plot_list[y][x].deleteLater()
        pass



    def del_ImgPrfSettingWidget_L(self):
        if self.imgprfwidget_xnum != 0:
            for i in np.arange(self.imgprfwidget_ynum,-1,-1):
                self.del_ImgPrfSettingWidget(i,-1)
                del self.img_plot_list[i][-1]
                time.sleep(1)
            # end
            self.imgprfwidget_xnum = self.imgprfwidget_xnum - 1
            self.update_ref_img_menu()
            self.update_row_analyze_table()
            # 【追加】analyze windowのhistの領域を伸長し直す
            # reset hist
            # self.analyze_window_ui.roi_hist_widget.clear()
            # for y in np.arange(0,self.imgprfwidget_ynum+1):
            #     for x in np.arange(0,self.imgprfwidget_xnum+1):
            #         self.analyze_window_ui.roi_hist_widget.addItem(self.img_plot_list[y][x].roi_hist,y,x) # analyze windowのhistplotエリア(MultiPlotWidget)にplotIttem追加
        pass

    def del_ImgPrfSettingWidget_U(self):
        if self.imgprfwidget_ynum != 0:
            for i in np.arange(self.imgprfwidget_xnum,-1,-1):
                self.del_ImgPrfSettingWidget(-1,i)
                time.sleep(1)
            # end
            del self.img_plot_list[-1]
            self.imgprfwidget_ynum = self.imgprfwidget_ynum - 1
            self.update_ref_img_menu()
            self.update_row_analyze_table()
            # 【追加】analyze windowのhistの領域を伸長し直す
        pass

    ####################################################################################################################
    #                                     Add Img by code
    ####################################################################################################################
    def overwrite_imageview_by_path(self, img_path, widget_y=0, widget_x=0):
        if self.imgprfwidget_ynum<widget_y:
            y_add = widget_y-self.imgprfwidget_ynum
            for i in np.arange(y_add):
                self.add_ImgPrfSettingWidget_B()
        if self.imgprfwidget_xnum<widget_x:
            x_add = widget_x-self.imgprfwidget_xnum
            for i in np.arange(x_add):
                self.add_ImgPrfSettingWidget_R()

        self.img_plot_list[widget_y][widget_x].img_path = img_path
        self.img_plot_list[widget_y][widget_x].read_img()
        self.img_plot_list[widget_y][widget_x].update_img()
        pass

    def overwrite_imageview_by_ndarray(self, img_array, widget_y=0, widget_x=0):
        if self.imgprfwidget_ynum<widget_y:
            y_add = widget_y-self.imgprfwidget_ynum
            for i in np.arange(y_add):
                self.add_ImgPrfSettingWidget_B()
        if self.imgprfwidget_xnum<widget_x:
            x_add = widget_x-self.imgprfwidget_xnum
            for i in np.arange(x_add):
                self.add_ImgPrfSettingWidget_R()

        self.img_plot_list[widget_y][widget_x].img_path = "ndarray"
        self.img_plot_list[widget_y][widget_x].input_img = img_array
        self.img_plot_list[widget_y][widget_x].update_img()
        pass

    def overwrite_imageview(self, img_list):
        if isinstance(img_list, list)==False:
            img_list = [img_list]

        img_num = len(img_list)# list length
        sub_x = np.ceil(np.sqrt(img_num)).astype(int)
        sub_y = np.ceil(img_num/sub_x).astype(int)
        i = 0
        for y in np.arange(sub_y):
            for x in np.arange(sub_x):
                if isinstance(img_list[i], str):
                    self.overwrite_imageview_by_path(img_list[i], y, x)
                elif type(img_list[i]).__module__ == np.__name__:
                    self.overwrite_imageview_by_ndarray(img_list[i], y, x)
                i = i + 1
        pass

    ####################################################################################################################
    #                                     interactive use
    ####################################################################################################################
    def get_imageview_image(self):
        out_list = []
        for y in np.arange(self.imgprfwidget_ynum+1):
            for x in np.arange(self.imgprfwidget_xnum+1):
                out_list.append(self.img_plot_list[y][x].img.image)
        return out_list




