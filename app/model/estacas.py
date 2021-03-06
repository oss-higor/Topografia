# -*- coding: utf-8 -*-
import csv
import math
import sqlite3

from qgis._core import QgsPoint

from ..model.config import extractZIP, Config, compactZIP
from ..model.curvas import Curvas
from ..model.utils import pairs, length, dircos, diff, azimuth, getElevation



from qgis.PyQt import QtGui

class Estacas:
    def __init__(self, distancia=20, estaca=0, layer=None, filename='', table=list(), ultimo=-1, id_filename=-1):
        self.distancia = distancia

        self.filename = filename
        self.estaca = estaca
        self.layer = layer
        self.table = table
        self.ultimo = ultimo
        self.id_filename = id_filename

    def get_features(self):
        linhas = []
        for feature in self.layer.getFeatures():
            geom = feature.geometry().asPolyline()
            for i in geom:
                linhas.append(i)
        return linhas

    def new(self, distancia, estaca, layer, filename):
        self.__init__(distancia, estaca, layer, filename, list(), self.ultimo, self.id_filename)

        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + filename + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
        con.close()
        compactZIP(Config.fileName)
        self.ultimo = id_estaca[0]
        self.table = self.create_estacas()

        return self.ultimo, self.table

    def getCurvas(self, id_filename):
        # instancia da model de curvas.
        curva_model = Curvas(id_filename)
        return curva_model.list_curvas()

    def getCRS(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        proj = con.execute("SELECT crs FROM PROJECT where id = 1").fetchone()
        crs = proj[0]
        con.close()
        compactZIP(Config.fileName)
        return crs

    def tipo(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        proj = con.execute(
            "SELECT crs, classeprojeto, maxplano,maxondulado,maxmontanhoso,tipomapa FROM PROJECT where id = 1").fetchone()

        class_project = proj[1]
        dataTopo = [
            0.0,
            proj[2],
            proj[2],
            proj[3],
            proj[3],
            proj[4]
        ]
        con.close()
        compactZIP(Config.fileName)
        return dataTopo, class_project

    def recalcular(self, distancia, estaca, layer):
        self.__init__(distancia, estaca, layer, self.filename, list(), self.ultimo, self.id_filename)
        self.table = self.create_estacas()
        return self.table

    def loadFilename(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        est = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def listTables(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        est = con.execute("SELECT id,name,data FROM TABLEESTACA").fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def deleteEstaca(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM TABLEESTACA WHERE id=?", (idEstacaTable,))
        con.commit()
        con.close()
        compactZIP(Config.fileName)

    def save(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.commit()
        for linha in self.table:
            linha.append(int(idEstacaTable))

            lt = tuple(linha)
            con.execute(
                "INSERT INTO ESTACA (estaca,descricao,progressiva,norte,este,cota,azimute,TABLEESTACA_id)values(?,?,REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),?)",
                lt)
        con.execute("VACUUM")
        con.commit()
        con.close()

        compactZIP(Config.fileName)

    def saveGreide(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM GREIDE")
        con.commit()
        for linha in self.table:

            lt = tuple(linha)

            con.execute(
                   "INSERT INTO GREIDE (x,cota)values(?,?)",
                   lt)

        con.execute("VACUUM")
        con.commit()
        con.close()

        compactZIP(Config.fileName)

        
    def openCSV(self, filename, fileDB):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + fileDB + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
        con.close()
        compactZIP(Config.fileName)
        self.ultimo = id_estaca[0]
        estacas = []
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        with open(filename, 'rb') as fi:
            for r in csv.reader(fi, delimiter=delimiter, dialect='excel'):
                estaca = []
                for field in r:
                    estaca.append(u"%s" % field)
                estacas.append(estaca)
        self.table = estacas

        return estacas

    def saveCSV(self, filename):
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        with open(filename, "wb") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
            for r in self.table:
                writer.writerow(r)

    def gera_vertice(self):
        prog = 0.0
        sobra = 0.0
        resto = 0.0
        estaca = 0
        cosa = 0.0
        cosb = 0.0
        crs = int(self.getCRS())
        sem_internet = False
        for elemento in self.layer.getFeatures():
            for i, (seg_start, seg_end) in enumerate(pairs(elemento, self.estaca)):
                ponto_inicial = QgsPoint(seg_start)
                ponto_final = QgsPoint(seg_end)
                tamanho_da_linha = length(ponto_final, ponto_inicial)
                ponto = diff(ponto_final, ponto_inicial)
                cosa, cosb = dircos(ponto)
                az = azimuth(ponto_inicial, QgsPoint(ponto_inicial.x() + ((self.distancia) * cosa),
                                                     ponto_inicial.y() + ((self.distancia) * cosb)))
                estacas_inteiras = int(math.floor((tamanho_da_linha - sobra) / self.distancia))
                estacas_inteiras_sobra = estacas_inteiras + 1 if sobra > 0 else estacas_inteiras
                if not sem_internet:
                    cota = getElevation(crs, QgsPoint(float(ponto_inicial.x()), float(ponto_inicial.y())))
                    if cota == 0:
                        sem_internet = True
                else:
                    cota = 0.0

                yield ['%d+%f' % (estaca, resto) if resto != 0 else '%d' % (estaca), 'v%d' % i, prog, ponto_inicial.y(),
                       ponto_inicial.x(), cota,
                       az], ponto_inicial, estacas_inteiras, prog, az, sobra, tamanho_da_linha, cosa, cosb

                prog += tamanho_da_linha
                resto = (tamanho_da_linha - sobra) - (self.distancia * estacas_inteiras)
                sobra = self.distancia - resto
                estaca += estacas_inteiras_sobra
            cota = getElevation(crs, QgsPoint(float(ponto_final.x()), float(ponto_final.y())))
            yield ['%d+%f' % (estaca, resto), 'v%d' % i, prog, ponto_final.y(), ponto_final.x(), cota,
                   az], ponto_final, 0, tamanho_da_linha, az, sobra, tamanho_da_linha, cosa, cosb

    def gera_estaca_intermediaria(self, estaca, anterior, prog, az, cosa, cosb, sobra=0.0):
        dist = sobra if sobra > 0 else self.distancia

        p = QgsPoint(anterior.x() + (dist * cosa), anterior.y() + (dist * cosb))
        prog += dist
        return [estaca, '', prog, p.y(), p.x(), 0.0, az], prog, p

    def create_estacas(self):
        estacas = []
        estaca = 0
        progressiva = 0
        for vertice, ponto_anterior, qtd_estacas, progressiva, az, sobra, tamanho_da_linha, cosa, cosb in self.gera_vertice():
            estacas.append(vertice)
            if sobra > 0 and sobra < self.distancia and qtd_estacas > 0:
                tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + 1, ponto_anterior,
                                                                                       progressiva, az, cosa, cosb,
                                                                                       sobra)
                estacas.append(tmp_line)
                estaca += 1

            for e in range(qtd_estacas):
                tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + e + 1, ponto_anterior,
                                                                                       progressiva, az, cosa, cosb)
                estacas.append(tmp_line)
            estaca += qtd_estacas
        return estacas

    def create_estacas_old(self):
        estacas = []
        k = 0
        prog = 0.0
        dist = 0.0
        p = self.get_features()[self.estaca]
        az = 0.0
        lab = 0
        for elem in self.layer.getFeatures():
            for i, (seg_start, seg_end) in enumerate(pairs(elem, self.estaca)):
                estaca = []
                line_start = QgsPoint(seg_start)
                line_end = QgsPoint(seg_end)
                if k != 0:
                    # lab = 1
                    pass
                else:

                    lab = 0

                # mid point = vector coordinates [x2-x1,y2-y1]
                pointm = diff(line_end, line_start)
                # direction cosines of the segment
                cosa, cosb = dircos(pointm)
                # length of the segment
                lg = length(line_end, line_start)
                az = azimuth(line_start, QgsPoint(line_start.x() + ((prog + self.distancia) * cosa),
                                                  line_start.y() + ((prog + self.distancia) * cosb)))

                geo = line_start
                prop = self.distancia - ((prog + self.distancia) - dist) if prog > 0 else prog
                txtId = "%d+%f" % (lab, prop) if prog > 0 or prop > 0 else "%d" % lab
                estaca.extend([txtId, 'v%d' % i, dist, geo.y(), geo.x(), 0.0, az])
                estacas.append(estaca)
                '''
                    ------------------------------------------------
                    Definição das estacas intermediarias.
                    ------------------------------------------------
                '''
                prog = 0.0 if (prog == 0) else prog
                dist = dist + lg
                p = line_start
                nprog = 0.0
                while nprog + self.distancia < lg:
                    estaca = []
                    lab += 1
                    k += 1
                    pa = p
                    p = QgsPoint(p.x() + ((self.distancia - prop) * cosa), p.y() + ((self.distancia - prop) * cosb))

                    az = azimuth(seg_start, p)
                    prog += self.distancia
                    nprog += self.distancia
                    prop = 0
                    estaca.extend([str(lab), '', prog, p.y(), p.x(), 0.0, az])
                    estacas.append(estaca)

        estaca = []
        ultimo = self.get_features()[-1]
        lg = prog + length(p, ultimo)
        prop = self.distancia - (prog - lg) if prog > 0 else prog
        txtId = "%d+%f" % (lab, prop) if prog > 0 or prop > 0 else "%d" % lab

        # az = self.azimuth(p,QgsPoint(ultimo.x(), ultimo.y()))

        estaca.extend([txtId, 'vf', lg, ultimo.y(), ultimo.x(), ultimo.x(), az])
        estacas.append(estaca)
        return estacas
