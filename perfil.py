# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_perfil.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import numpy as np
import pyqtgraph as pg





class CustomViewBox(pg.ViewBox):
      def __init__(self, *args, **kwds):
          pg.ViewBox.__init__(self, *args, **kwds)
          self.setMouseMode(self.RectMode)
          
      ## reimplement mid-click to zoom out
      def mouseClickEvent(self, ev):
          if ev.button() == QtCore.Qt.MidButton:
              self.autoRange()

      def mouseDragEvent(self, ev):
          if ev.button() == QtCore.Qt.RightButton:
              ev.ignore()
          else:
              pg.ViewBox.mouseDragEvent(self, ev)


class CustomPolyLineROI(pg.PolyLineROI):
    def __init__(self, *args, **kwds):
        pg.PolyLineROI.__init__(self,*args,**kwds)


    def setPoints(self, points, closed=None):

        if closed is not None:
            self.closed = closed
        
        self.clearPoints()
        
        for p in points:
            self.addRotateHandle(p,p)
            
        start = -1 if self.closed else 0
        for i in range(start, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item']) 
        



    def segmentClicked(self, segment, ev=None, pos=None): ## pos should be in this item's coordinate system
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        if ev.button() == QtCore.Qt.RightButton:
            pass
        else:
            h1 = segment.handles[0]['item']
            h2 = segment.handles[1]['item']
            
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i+1)
            segment.replaceHandle(h2, h3)
            


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


   
   
class Ui_Perfil(QtGui.QDialog):
    save = QtCore.pyqtSignal()
    def __init__(self, ref_estaca, tipo, classeProjeto):
        super(Ui_Perfil, self).__init__(None)
        self.ref_estaca = ref_estaca
        self.tipo = tipo
        self.classeProjeto = classeProjeto
        self.estaca1txt = -1
        self.estaca2txt = -1
        self.vb=CustomViewBox() 
        self.perfilPlot = pg.PlotWidget(viewBox=self.vb,  enableMenu=False, title="Perfil Longitudinal")

        self.setupUi(self)

  

    def perfil_grafico(self):
        pontos = []
        k = 0
        while True:
            try:
                ponto = []
                e = self.ref_estaca.tableWidget.item(k,0).text()
                if e in [None,""]:
                    break
                ponto.append(float(self.ref_estaca.tableWidget.item(k,2).text()))
                ponto.append(float(self.ref_estaca.tableWidget.item(k,5).text()))
                pontos.append(ponto)
                self.comboEstaca1.addItem(_fromUtf8(e))
            except:
                break
            k += 1
       
        x,y=zip(*pontos)
        x=list(x)
        y=list(y)       
        
        
        self.perfilPlot.plot(x=x, y=y, symbol='o')

        self.perfilPlot.setWindowTitle('pyqtgraph example: customPlot')
        A = np.array([x,np.ones(len(x))])
        w = np.linalg.lstsq(A.T,y)[0]
        r = CustomPolyLineROI([(x[0],w[0]*x[0]+w[1]), (x[len(x)-1],w[0]*x[len(x)-1]+w[1])])
        r.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.perfilPlot.addItem(r)
        self.greide=r



    def calcI(self,p1, p2):
    
        try:
            prog1 = float(self.ref_estaca.tableWidget.item(p1, 2).text())
            prog2 = float(self.ref_estaca.tableWidget.item(p2, 2).text())

            cota1 = float(self.ref_estaca.tableWidget.item(p1, 5).text())
            cota2 = float(self.ref_estaca.tableWidget.item(p2, 5).text())
            return ((cota2 - cota1) / (prog2 - prog1)) * 100
        except:
            return 0

    def calcular(self):

        p1 = self.calcI(self.estaca1txt,self.estaca2txt)
        classeProjeto = self.classeProjeto
        if p1>=float(self.tipo[0]) and p1<float(self.tipo[1]):
            if classeProjeto<=0:
                s = "120"
            elif classeProjeto <4:
                s = "100"
            elif classeProjeto <6:
                s = "80"
            else:
                s = "60"
            self.lblTipo.setText("Plano %s KM/h"%(s))
         #   for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
         #       for j in range(self.ref_estaca.tableWidget.columnCount()):
         #           self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(51,153,255))

        elif p1>=float(self.tipo[2]) and p1<float(self.tipo[3]):
            if classeProjeto<=0:
                s = "100"
            elif classeProjeto <3:
                s = "80"
            elif classeProjeto <4:
                s = "70"
            elif classeProjeto <6:
                s = "60"
            else:
                s = "40"
            self.lblTipo.setText("Ondulado %s KM/h"%(s))
            for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
                for j in range(self.ref_estaca.tableWidget.columnCount()):
                    self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,253,150))
        else:
            if classeProjeto<=0:
                s = "80"
            elif classeProjeto <3:
                s = "60"
            elif classeProjeto <4:
                s = "50"
            elif classeProjeto <6:
                s = "40"
            else:
                s = "30"
            self.lblTipo.setText("Montanhoso %s KM/h"%(s))
          #  for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
          #      for j in range(self.ref_estaca.tableWidget.columnCount()):
          #          self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,51,51))




    def calcularGreide(self):
        self.greide.getMenu()
        i=0
        g1=[]
        g2=[]
        for handle in self.greide.getHandles():
            if i==0:
                g1.append(handle.scenePos().x())
                g1.append(handle.scenePos().y())
            if i==1:

                g2.append(handle.scenePos().x())
                g2.append(handle.scenePos().y())
    
            if i>1:
                break
            i+=1
                

        p1 =abs((g1[1] - g2[1]) / (g1[0] - g2[0])) * 100
        classeProjeto = self.classeProjeto
        if p1>=float(self.tipo[0]) and p1<float(self.tipo[1]):
            if classeProjeto<=0:
                s = "120"
            elif classeProjeto <4:
                s = "100"
            elif classeProjeto <6:
                s = "80"
            else:
                s = "60"
            self.lblTipo.setText("Plano %s KM/h"%(s))
            for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
                for j in range(self.ref_estaca.tableWidget.columnCount()):
                    self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(51,153,255))

        elif p1>=float(self.tipo[2]) and p1<float(self.tipo[3]):
            if classeProjeto<=0:
                s = "100"
            elif classeProjeto <3:
                s = "80"
            elif classeProjeto <4:
                s = "70"
            elif classeProjeto <6:
                s = "60"
            else:
                s = "40"
            self.lblTipo.setText("Ondulado %s KM/h"%(s))
 #           for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
 #               for j in range(self.ref_estaca.tableWidget.columnCount()):
 #                   self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,253,150))
        else:
            if classeProjeto<=0:
                s = "80"
            elif classeProjeto <3:
                s = "60"
            elif classeProjeto <4:
                s = "50"
            elif classeProjeto <6:
                s = "40"
            else:
                s = "30"
            self.lblTipo.setText("Montanhoso %s KM/h"%(s))
 #           for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
#                for j in range(self.ref_estaca.tableWidget.columnCount()):
#                    self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,51,51))


    def estaca1(self,ind):
        self.estaca1txt = ind-1

    def estaca2(self,ind):
        self.estaca2txt = ind-1

    def setupUi(self, PerfilTrecho):

    
        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(590, 169)
        self.comboEstaca1 = QtGui.QComboBox(PerfilTrecho)
        self.comboEstaca1.setGeometry(QtCore.QRect(100, 20, 181, 31))
        self.comboEstaca1.setObjectName(_fromUtf8("comboEstaca1"))
        self.comboEstaca1.addItem(_fromUtf8(""))
        k = 0
        while True:
            try:
                e = self.ref_estaca.tableWidget.item(k,0).text()
                if e in [None,""]:
                    break
                self.comboEstaca1.addItem(_fromUtf8(e))
            except:
                break
            k += 1
        self.comboEstaca1.currentIndexChanged.connect(self.estaca1)

        self.label = QtGui.QLabel(PerfilTrecho)
        self.label.setGeometry(QtCore.QRect(20, 26, 68, 21))
        self.label.setObjectName(_fromUtf8("label"))

        self.comboEstaca2 = QtGui.QComboBox(PerfilTrecho)
        self.comboEstaca2.setGeometry(QtCore.QRect(390, 20, 181, 31))
        self.comboEstaca2.setObjectName(_fromUtf8("comboEstaca2"))
        self.comboEstaca2.addItem(_fromUtf8(""))
        k = 0
        while True:
            try:
                e = self.ref_estaca.tableWidget.item(k, 0).text()
                if e in [None, ""]:
                    break
                self.comboEstaca2.addItem(_fromUtf8(e))
            except:
                break
            k += 1
        self.perfil_grafico()
        self.comboEstaca2.currentIndexChanged.connect(self.estaca2)


        self.label_2 = QtGui.QLabel(PerfilTrecho)
        self.label_2.setGeometry(QtCore.QRect(310, 26, 68, 21))
        self.label_2.setObjectName(_fromUtf8("label_2"))

        self.lblTipo = QtGui.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtGui.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.calcular)
        
        self.btnAutoRange=QtGui.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Auto")

        self.btnSave=QtGui.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Save")
        self.btnSave.clicked.connect(self.salvarPerfil)



        Hlayout=QtGui.QHBoxLayout()
        Vlayout=QtGui.QVBoxLayout()

        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)

        Hlayout.addWidget(self.comboEstaca1)
        Hlayout.addWidget(self.label)
        Hlayout.addWidget(self.comboEstaca2)
        Hlayout.addWidget(self.label_2)
        Hlayout.addWidget(self.lblTipo)
        Hlayout.addWidget(self.btnCalcular)
        Vlayout.addWidget(self.btnAutoRange) 
        Vlayout.addWidget(self.btnSave) 

        Vlayout.addLayout(Hlayout)
        Vlayout.addWidget(self.perfilPlot)

        self.showMaximized()

        self.greide.sigClicked.connect(self.calcularGreide)

        self.setLayout(Vlayout)          
        self.retranslateUi(PerfilTrecho)




    def salvarPerfil(self):
        #exportar greide para csv e referenciar no banco de dados
        ##sinal emitido para salvar

        self.save.emit()

    def getVertices(self):

        r=[]
        for handle in self.greide.getHandles():
           x=[]
           x.append(str(handle.scenePos().x())) 
           x.append(str(handle.scenePos().y())) 
           r.append(x)
        
        return r


    def retranslateUi(self, PerfilTrecho):
        PerfilTrecho.setWindowTitle(_translate("PerfilTrecho", "Perfil do trecho", None))
        self.comboEstaca1.setItemText(0, _translate("PerfilTrecho", "Selecione Estaca Inicial", None))
        self.label.setText(_translate("PerfilTrecho", "Estaca 1", None))
        self.comboEstaca2.setItemText(0, _translate("PerfilTrecho", "Selecione Estaca Final", None))
        self.label_2.setText(_translate("PerfilTrecho", "Estaca 2", None))
        self.lblTipo.setText(_translate("PerfilTrecho", "Plano", None))
        self.btnCalcular.setText(_translate("PerfilTrecho", "Calcular", None))


