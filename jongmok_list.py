import sys

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtGui import *

class Kiwoom(QMainWindow):
	def __init__(self):
		super().__init__()
		self.initUI()
		self.login()
		self.sMarket = "0" # default: kospi

	def initUI(self):
		self.setWindowTitle("종목검색")
		self.setGeometry(300, 300, 800, 600)

		self.statusBar().showMessage("Not Connected")

		self.Market_combo = QComboBox(self)
		self.Market_combo.addItem('코스피')
		self.Market_combo.addItem('코스닥')
		self.Market_combo.setGeometry(20, 20, 130, 30)
		self.Market_combo.activated[str].connect(self.market_combo_activated)

		self.JongMok_button = QPushButton('종목조회', self)
		self.JongMok_button.move(160, 20)
		self.JongMok_button.clicked.connect(self.jongmok_button_clicked)
		self.JongMok_button.setFocus()
		self.JongMok_button.setEnabled(False)

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

	def market_combo_activated(self, text):
		if text == "코스피":
			self.sMarket = "0"		# kospi
		else:
			self.sMarket = "10"		# kosdak

	def event_connect(self, err_code):
		if err_code == 0:
			self.statusBar().showMessage("Connected")
			self.JongMok_button.setEnabled(True)
		else:
			self.statusBar().showMessage("Connection Failed (err:%d)" % err_code)

	def jongmok_button_clicked(self):
		self.JongMok_result.clear()
		ret = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", [self.sMarket])
		code_list = ret.split(';')
		if len(code_list) > 1:
			code_list = code_list[:-1] # remove last null item due to split(';')
		name_list = []
		count = 0

		for x in code_list:
			count = count + 1
			name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", [x])
			name_list.append(x + " : " + name)
			self.JongMok_result.append(str(count) + " " + x + " : " + name)
		self.JongMok_result.append("전체: " + str(len(name_list)) + " 개 검색")

if __name__ == "__main__":
	app = QApplication(sys.argv)
	myWindow = Kiwoom()
	myWindow.show()
	app.exec_()
