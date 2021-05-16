# Readme
![qqri_icon1](https://user-images.githubusercontent.com/47070478/117133652-7ceab180-addf-11eb-8492-e6a4789c37f1.png)  
日本語のreadmeは下にあります。  

For those who have difficulty installing Python or its libraries, we have prepared an environment for distribution using "embeddable python". (windows 64bit only)  
The download link is below.  
Unzip the python-3.9.5-embed-amd64_QQRIviewer.zip file and change directory at the command prompt.  
You can then use the Q.Q.R.I.viewer by typing "python QQRIviewer_use_sample.py" at the command prompt.  
  
Pythonもしくはライブラリのインストールが困難な方のために、「embeddable python」を使用した配布用環境を用意してあります。(windows 64bitのみ)  
ダウンロードリンクは下記です。  
python-3.9.5-embed-amd64_QQRIviewer.zipファイルを解凍し、コマンドプロンプト上でそのディレクトリに移動してください。  
その状態でコマンドプロンプトで「python QQRIviewer_use_sample.py」とタイプすれば、Q.Q.R.I.viewerを使用することができます。  
  
Download：https://drive.google.com/file/d/17GcbxSek_2uMMDq_nCcpE6NeqJzOPWFR/view?usp=sharing



# Q.Q.R.I.viewer  
Q.Q.R.I.viewer is an open source image viewing and image analysis program implemented using Python 3 (PyQt5).  
We created it because we wanted an image viewer with quick response, direct data transfer from Python, and image analysis capability.  
("Q.Q.R.I.viewer" is an abbreviation for pyQt-based Quick Response Image viewer.Pronounce it "kukuri viewer".)  

## Functions of Q.Q.R.I.viewer  
### Multiple image loading methods for multiple image formats.  
Q.Q.R.I.viewer can read images that are supported by Pillow (PIL fork) and 8bit/16bit/32bit binary format images.  
(Supported image formats:BMP,EPS,GIF,ICNS,IM,JPEG,JPEG2000,MSP,PCX,PNG,PPM,SPIDER,TIFF,WebP,XBM,CUR,DCX,DDS,FLI,FLC,FPX,FTEX,GBR,GD,ICO,IMT, IPTC/NAA, MCIDAS, MIC, MPO, PCD, PIXAR, PSD, SGI, TGA, WAL, XPM)  

The following methods can be used to load images.  
- Passing a path from Python code as an argument  
- Passing an ndarray from the Python code as an argument  
- Drag and drop  
![text7556-10](https://user-images.githubusercontent.com/47070478/117116500-68032380-adc9-11eb-8162-c4f09c4f1e43.png)


### Multiple image display and image analysis tools with synchronized behavior
Q.Q.R.I.viewer's main window can display multiple widgets called "image view", and their behaviors are linked to each other.   
The image view can be increased or decreased.  
![imgview_add_del](https://user-images.githubusercontent.com/47070478/117156993-2b4f2080-adf9-11eb-8269-0b8a811a280e.gif)  


The main functions of "image view" are as follows.  
![g8218](https://user-images.githubusercontent.com/47070478/117118478-c4ffd900-adcb-11eb-9c38-637a62aca6c2.png)

#### (1) Image display  
The image can be moved by dragging the left mouse button, and enlarged or reduced by dragging the mouse wheel or right mouse button.  
Also, the behavior is synchronized among multiple image views.   
![imgmove2](https://user-images.githubusercontent.com/47070478/117132941-87f11200-adde-11eb-8433-1f9ce47a841d.gif)  


#### (2) Histogram of the entire image  
Displays the histogram of the entire image by channel.  

#### (3) Level correction function of the displayed image  
This function adjusts the black/white level of the image display.  
It can be adjusted by dragging the slider superimposed on the histogram of the entire image, or by entering numerical values in the black/white level value specification box.  
![level](https://user-images.githubusercontent.com/47070478/117131933-16649400-addd-11eb-9373-09ccf74a8e52.gif)  


#### (4) Pseudo color selection for 1ch image and color bar display
You can specify the pseudo color to be used for displaying the 1ch image from the drop-down list.   
The color bar of the specified pseudo color will be displayed below the histogram of the entire image.  
![pcolor](https://user-images.githubusercontent.com/47070478/117131640-a35b1d80-addc-11eb-85b2-29f180a2341b.gif)  


#### (5) Line of Interest (LOI) & Profile Display  
Add a new LOI with the shotcut key <t>, and the profile on the LOI will be displayed above (horizontal LOI) and to the right (vertical LOI) of the image view.  
The behavior of LOI is synchronized among multiple image views.  
![loi2](https://user-images.githubusercontent.com/47070478/117131448-698a1700-addc-11eb-966f-7ea571402b6f.gif)  


#### (6) Region of Interest (ROI)  
You can add a new ROI by pressing the shot cut key <r>.  
The histogram and statistics of the ROI will be displayed in the analyze window.  
The behavior of the ROI is synchronized among multiple image views.  
![roi](https://user-images.githubusercontent.com/47070478/117131143-026c6280-addc-11eb-9ebb-dddb1d072fe0.gif)  

## Interactively manipulating the Q.Q.R.I. viewer from a Python shell
If you run QQRIviewer_use_sample.py, it will not accept input from the Python shell.    
This is normal behavior according to the PyQt5 specification, but there may be times when you want to interactively control the Q.Q.R.I. viewer from a Python shell.  
In this case, run "QQRIviewer_use_sample_interactive.py" as shown below.  
  
```
python -i QQRIviewer_use_sample_interactive.py
```

Alternatively, start a Python shell and run the following one line at a time.   
``` 
$> python  
>>>from PyQt5.QtWidgets import QApplication
>>>import QQRIviewer as qv
>>>app = QApplication([])
>>>qqri = qv.QqriWindow()
>>>qqri.show()
>>>qqri.raise_()  
```
  

## Required Libraries  
- PyQt5  
- pyqtgraph  
- numpy  
- Pillow  
- matplotlib  
(and the libraries needed to use these libraries)  


## In the future
I will continue to work on the development of a quick response image viewer.  
If there are any bugs or features you would like to see added, please let me know.  
I am also looking for members who are willing to develop Q.Q.R.I.viewer with me.  

### Features to be added in the future
Faster image loading  
Specify a reference image and compare it with other images (PSNR, SSIM, similarity, etc.)  
Simple image processing simulation (blurring, sharpening, gamma, etc.)  

---

以下、日本語

---
# Q.Q.R.I.viewer
Q.Q.R.I.viewerは、Python3(PyQt5)を用いて実装されたオープンソースの画像閲覧&画像解析プログラムです。  
高速レスポンスかつPythonから直接データを渡せて、画像解析可能な画像ビューアが欲しかったので作りました。  
(「Q.Q.R.I.viewer」は、pyQt-based Quick Response Image viewer の略称です。「ククリビューア」と読んでください。)  


## Q.Q.R.I.viewerの機能
### 複数の画像フォーマットに対応した、複数の画像読み込み方式  
Q.Q.R.I.viewerは、Pillow(PIL fork)が対応している画像と8bit/16bit/32bitのバイナリ形式画像を読み込むことができます。  
(対応している画像フォーマット：BMP,EPS,GIF,ICNS,IM,JPEG,JPEG2000,MSP,PCX,PNG,PPM,SPIDER,TIFF,WebP,XBM,CUR,DCX,DDS,FLI,FLC,FPX,FTEX,GBR,GD,ICO,IMT,IPTC/NAA,MCIDAS,MIC,MPO,PCD,PIXAR,PSD,SGI,TGA,WAL,XPM)   

以下の方法で画像を読み込むことができます。  
- Pythonコードからパスを引数として渡す  
- Pythonコードからndarrayを引数として渡す  
- ドラッグ&ドロップ  
 ![text7556-10](https://user-images.githubusercontent.com/47070478/117116500-68032380-adc9-11eb-8162-c4f09c4f1e43.png)  


### 挙動が同期した、複数の画像表示と画像解析ツール
Q.Q.R.I.viewerのmain windowは「image view」というウィジェットを複数表示することができ、それぞれの挙動はリンクしています。  
image viewは増減させることができます。  
![imgview_add_del](https://user-images.githubusercontent.com/47070478/117156993-2b4f2080-adf9-11eb-8269-0b8a811a280e.gif)  

「image view」の主な機能は以下の通りです。  
![g8218](https://user-images.githubusercontent.com/47070478/117118478-c4ffd900-adcb-11eb-9c38-637a62aca6c2.png)  

#### (1)画像表示機能  
左ドラッグで画像の移動、マウスホイールもしくは右ドラッグで拡大縮小ができます。  
また、複数のimage view間で挙動が同期します。  
![imgmove2](https://user-images.githubusercontent.com/47070478/117132941-87f11200-adde-11eb-8433-1f9ce47a841d.gif)  


#### (2)画像全体のヒストグラム表示  
画像全体のヒストグラムをチャンネル別に表示します。  

#### (3)表示画像のレベル補正機能  
画像表示の黒/白レベルを調整する機能です。  
画像全体のヒストグラムに重畳するスライダーのドラッグ、もしくは黒/白レベル数値指定ボックスへの数値入力で調整可能です。  
![level](https://user-images.githubusercontent.com/47070478/117131933-16649400-addd-11eb-9373-09ccf74a8e52.gif)  


#### (4)1ch画像に対するカラープロット選択と、カラーバー表示  
1ch画像の表示に使用する疑似カラーをドロップダウンリストから指定することができます。  
画像全体のヒストグラムの下に、指定した疑似カラーのカラーバーが表示されます。  
![pcolor](https://user-images.githubusercontent.com/47070478/117131640-a35b1d80-addc-11eb-85b2-29f180a2341b.gif)  


#### (5)Line of Interest(LOI) & プロファイル表示  
ショットカットキー<t>で新規LOIを追加し、LOI上のプロファイルをimage viewの上方(水平LOI)と右方(垂直LOI)に表示します。  
またLOIは、複数のimage view間で挙動が同期します。  
![loi2](https://user-images.githubusercontent.com/47070478/117131448-698a1700-addc-11eb-966f-7ea571402b6f.gif)  


#### (6)Region of Interest(ROI)  
ショットカットキー<r>で新規ROIを追加することができます。  
analyze windowにROI部分のヒストグラム、統計量を表示します。  
またROIは、複数のimage view間で挙動が同期します。  
![roi](https://user-images.githubusercontent.com/47070478/117131143-026c6280-addc-11eb-9ebb-dddb1d072fe0.gif)  


## PythonシェルからQ.Q.R.I.viewerをインタラクティブに操作する  
QQRIviewer_use_sample.pyを実行した場合、Pythonシェルからの入力を受け付けなくなります。  
これはPyQt5仕様上正常な動作ですが、PythonシェルからQ.Q.R.I.viewerをインタラクティブに操作したい場合もあると思われます。  
その場合は「QQRIviewer_use_sample_interactive.py」を下記のように実行してください。  
  
```
python -i QQRIviewer_use_sample_interactive.py  
```

もしくはPythonシェル起動後、下記を1行づつ実行してください。  
``` 
$> python  
>>>from PyQt5.QtWidgets import QApplication
>>>import QQRIviewer as qv
>>>app = QApplication([])
>>>qqri = qv.QqriWindow()
>>>qqri.show()
>>>qqri.raise_()  
```

## 必要なライブラリ
- PyQt5  
- pyqtgraph  
- numpy  
- Pillow  
- matplotlib  
(またこれらのライブラリを使用するために必要なライブラリ)  

## 今後
高速なレスポンスの画像ビューアを目指して開発を続けて行きます。  
もしバグや追加してほしい機能があれば、積極的に教えて下さい。  
また、一緒に開発をしてくれるメンバーも募集しています。  

### 今後追加予定の機能
画像読み込みの高速化  
リファレンス画像を指定し、他の画像との比較(PSNR、SSIM、類似度等)  
簡易な画像処理シミュレーション(ぼかし、先鋭化、ガンマ等)  
  

## 検索用 
python 画像ビューア 画像ビューワ 画像ビューワー 画像処理 画像解析 PyQt5  
python image viewer data viewer image processing image analyzing  
