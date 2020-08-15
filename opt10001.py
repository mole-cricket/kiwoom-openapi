import sys
import time
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtGui import *

class MyLineEdit(QLineEdit):
	def focusInEvent(self, event):
		if self.text() == "종목코드를 입력하세요":
			self.setText('')
			self.setMaxLength(6)
		super(MyLineEdit, self).focusInEvent(event)

class Kiwoom(QMainWindow):
	def initUI(self):
		self.setWindowTitle("Opt10001")
		self.setGeometry(300, 300, 800, 600)

		self.statusBar().showMessage("Not Connected")

		self.JongMok_label = QLabel('종목코드:', self)
		self.JongMok_label.move(20, 20)

		self.JongMok_lineedit = MyLineEdit(self)
		self.JongMok_lineedit.setGeometry(130, 20, 200, 30)
		self.JongMok_lineedit.setText('종목코드를 입력하세요')

		self.JongMok_button = QPushButton('조회', self)
		self.JongMok_button.move(350, 20)
		self.JongMok_button.clicked.connect(self.jongmok_button_clicked)
		self.JongMok_button.setFocus()

		self.JongMok_result = QTextEdit(self)
		self.JongMok_result.setGeometry(10, 60, 780, 500)
		self.JongMok_result.setEnabled(True)

	def login(self):
		# Connect
		self.kiwoom = QAxWidget()
		self.kiwoom.setControl("KHOPENAPI.KHOpenAPICtrl.1")
		self.kiwoom.dynamicCall("CommConnect()")

		# OpenAPI+ Event
		self.kiwoom.OnEventConnect.connect(self.event_connect)
		self.kiwoom.OnReceiveTrData.connect(self.receive_tr_data)

	def __init__(self):
		super().__init__()
		self.initUI()
		self.login()

	def event_connect(self, err_code):
		if err_code == 0:
			self.statusBar().showMessage("Connected")
		else:
			self.statusBar().showMessage("Connection Failed (err:%d)" % err_code)

	def jongmok_button_clicked(self):
		code = self.JongMok_lineedit.text()
		self.JongMok_result.append("종목코드:" + code)

		# SetInputValue
		self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드",  code)
		# CommRqData
		self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)",
								"opt10001_req", "opt10001", 0, "0101")

	def receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
		print("리시브로 들어옴 err_code:%s, msg1=%s, msg2=%s"%(err_code, msg1, msg2))
		if rqname == "opt10001_req":
			name = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString",
										   trcode, recordname, 0, "종목명")
			volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString",
											 trcode, recordname, 0, "거래량")
			numStocks = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString",
											 trcode, recordname, 0, "상장주식")
			prices = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString",
											 trcode, recordname, 0, "시가")

			self.JongMok_result.append("종목명:" + name.strip())
			self.JongMok_result.append("거래량:" + volume.strip())
			self.JongMok_result.append("상장주식:" + numStocks.strip())
			self.JongMok_result.append("시가:" + prices.strip())


if __name__=="__main__":
	app = QApplication(sys.argv)
	myWindow = Kiwoom()
	myWindow.show()
	app.exec_()