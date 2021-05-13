# 標準ライブラリ
from pathlib import Path
import urllib.parse
import time

# サードパーティーライブラリ
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from PIL import Image, ImageFile
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

        self.setWindowTitle("Enter the path of the image to be swapped.")
        layout = QtWidgets.QFormLayout()

        self.radio_btn_list = []
        self.radio_btn_list.append(QtWidgets.QRadioButton("RGB"))
        self.radio_btn_list.append(QtWidgets.QRadioButton("YUV422(8bit)"))
        self.radio_btn_list[0].setChecked(True)

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

        # hist表示
        self.hist_widget = pg.MultiPlotWidget()
        self.setting_layout.addWidget(self.hist_widget, 0, 0, 1,10)
        self.img_hist = self.hist_widget.addPlot(0,0)
        self.img_hist.showGrid(x=True, y=True, alpha=0.8)

        self.img_hist_plot0 = pg.PlotDataItem(np.array([0, 0, 0]), np.array([0, 0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(255,10,10),width=2))
        self.img_hist_plot1 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,255,10),width=2))
        self.img_hist_plot2 = pg.PlotDataItem(np.array([0,0,0]), np.array([0,0]),
                                              stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,10,255),width=2))
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
        self.colorbar_p = self.hist_widget.addPlot(1,0)
        self.colorbar = pg.ImageItem()
        self.colorbar.setOpts(axisOrder='row-major')
        self.colorbar_p.addItem(self.colorbar)
        self.colorbar_p.setMouseEnabled(x=False, y=False)
        self.colorbar_p.hideAxis('left')
        self.colorbar_p.hideAxis('bottom')

        # setting領域 : max,minの入力用
        view_min_label = QtWidgets.QLabel()
        view_min_label.setText("view-min")
        view_min_label.setAlignment(QtCore.Qt.AlignCenter)
        self.setting_layout.addWidget(view_min_label, 1, 0)
        self.view_min_text = QtWidgets.QLineEdit()
        self.setting_layout.addWidget(self.view_min_text, 1, 1)

        view_max_label = QtWidgets.QLabel()
        view_max_label.setText("view-max")
        view_max_label.setAlignment(QtCore.Qt.AlignCenter)
        self.setting_layout.addWidget(view_max_label, 1, 2)
        self.view_max_text = QtWidgets.QLineEdit()
        self.setting_layout.addWidget(self.view_max_text, 1, 3)

        # setting領域 ： colormap
        self.colormap_name_list = ['gray', 'viridis', 'jet', 'spring', 'summer', 'autumn', 'winter', 'cool', 'hot', 'coolwarm',
                                   'gnuplot', 'gnuplot2', 'plasma', 'inferno', 'magma', 'cividis', 'hsv', 'ocean',
                                   'twilight', 'twilight_shifted', 'seismic', 'copper', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20']
        self.colormap_cb = QtWidgets.QComboBox()
        self.colormap_cb.addItems(self.colormap_name_list)
        self.setting_layout.addWidget(self.colormap_cb, 1, 4)
        self.colormap_cb.currentIndexChanged.connect(self.set_colormap)

        # ch_swap
        self.ch_swap_btn = QtWidgets.QPushButton("ch swap", self)
        self.setting_layout.addWidget(self.ch_swap_btn, 1, 5)

        # setting領域コネクト
        self.hist_region.sigRegionChangeFinished.connect(self.update_img_level_by_region)
        self.view_min_text.editingFinished.connect(self.update_img_level_by_text)
        self.view_max_text.editingFinished.connect(self.update_img_level_by_text)
        self.ch_swap_btn.clicked.connect(self.ch_swap)

        pass


    def ch_swap(self):
        while True:
            csd = ch_swap_Dialog()
            path_0ch,path_1ch,path_2ch,img_format = csd.getdata()
            if path_0ch=='cancel':
                print('cancel')
                break
            else:
                print('koko')
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
                        if img_format=='YUV422(8bit)':
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
                        elif img_format=='RGB':
                            self.input_img = np.zeros((np.shape(temp_img_0ch)[0],np.shape(temp_img_0ch)[1],3))
                            self.input_img[:,:,0] = temp_img_0ch
                            self.input_img[:,:,1] = temp_img_1ch
                            self.input_img[:,:,2] = temp_img_2ch
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
    def update_img(self):

        # image 更新
        self.img.setImage(self.input_img)
        self.img.setRect(pg.QtCore.QRectF(-0.5, -0.5, np.shape(self.input_img)[1], np.shape(self.input_img)[0]))
        self.tmb_img.setImage(self.input_img)
        self.img_ch = None
        if np.ndim(self.img.image) == 3 and np.shape(self.img.image)[2] == 3:
            self.img_ch = 3
        elif np.ndim(self.img.image) == 2:
            self.img_ch = 1


        #
        self.img_path_str = str(self.img.image)
        self.view_max_in = np.max(self.img.image)
        self.view_min_in = np.min(self.img.image)
        self.img_is_stored = True

        # hist更新
        if self.img_ch == 3:
            y, x = np.histogram(self.img.image[:, :, 0], range=[self.view_min_in,self.view_max_in+1], bins=np.arange(self.view_min_in,self.view_max_in+2))
            self.img_hist_plot0.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(255,10,10),width=2))

            y, x = np.histogram(self.img.image[:, :, 1], range=[self.view_min_in,self.view_max_in+1], bins=np.arange(self.view_min_in,self.view_max_in+2))
            self.img_hist_plot1.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(10,255,10),width=2))

            y, x = np.histogram(self.img.image[:, :, 2], range=[self.view_min_in,self.view_max_in+1], bins=np.arange(self.view_min_in,self.view_max_in+2))
            self.img_hist_plot2.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color=(50,100,255),width=2))

            #【追加】ーcolorbarがある場合、削除する関数実行
        elif self.img_ch == 1:
            y, x = np.histogram(self.img.image, range=[self.view_min_in,self.view_max_in+1], bins=np.arange(self.view_min_in,self.view_max_in+2))
            self.img_hist_plot0.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))
            self.img_hist_plot1.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))
            self.img_hist_plot2.setData(x=x, y=y, stepMode=True, fillLevel=0, pen=pg.mkPen(color="w",width=2))
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
        colormap_N=256
        cm = get_cmap(self.colormap_cb.currentText(),colormap_N)
        self.colormap_lut = (np.array([cm(i) for i in range(colormap_N)]) * 255)
        self.img.setLookupTable(self.colormap_lut)
        self.colorbar.setImage(np.tile(self.colormap_lut[:,0:3],[100,1,1]).astype(np.uint8))
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


    def init_layout(self):
        #
        self.centerWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centerWidget)
        self.layout = QtWidgets.QGridLayout()
        self.centerWidget.setLayout(self.layout)

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

                # analyze window関連
                img_size = np.shape(self.img_plot_list[y][x].img.image)
                pos_s = (np.clip((np.round(pos[0]+0.5)).astype(int),0, img_size[1]), np.clip((np.round(pos[1]+0.5)).astype(int),0, img_size[0]))
                pos_e = (np.clip(pos_s[0]+size[0], 0, img_size[1]).astype(int), np.clip(pos_s[1]+size[1], 0, img_size[0]).astype(int))
                self.img_plot_list[y][x].img_roi[id].roi_pos  = [[pos_s[1], pos_e[1]], [pos_s[0], pos_e[0]]]
                self.img_plot_list[y][x].img_roi[id].roi_size = [pos_e[1]-pos_s[1], pos_e[0]-pos_s[0]]
                self.img_plot_list[y][x].img_roi[id].roi_pix  = self.img_plot_list[y][x].img_roi[id].roi_size[0]*self.img_plot_list[y][x].img_roi[id].roi_size[1]
                table_y_start = int(y*(self.imgprfwidget_xnum+1)+x)*len(self.img_plot_list[y][x].img_roi[id].roi_stats_func.keys())
                table_x_start = int(2+id*3)

                if (self.img_plot_list[y][x].img.image is None) or (self.img_plot_list[y][x].img_roi[id].roi_pix<=0):# 画像が入ってない場合
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot0.setData(np.array([0,1]), np.array([0]))
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot1.setData(np.array([0,1]), np.array([0]))
                    self.img_plot_list[y][x].img_roi[id].roi_hist_plot2.setData(np.array([0,1]), np.array([0]))
                else:# 画像がある場合
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




