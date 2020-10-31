#############################################################
# Search Company
#############################################################

import pandas as pd
from pandas import DataFrame
import requests
import sqlite3
from datetime import datetime

dbPath = "c:/StockDB/"
stockDb = "myStock.db"

# quarterly performance table info
qp_table = "q_perf_report"
qp_field = [ "종목코드", "분기", "매출액", "영업이익", "당기순이익",
			 "영업이익률", "순이익률", "ROE", "부채비율", "당좌비율",
			 "유보율", "EPS", "PER", "BPS", "PBR" ]
codeDataName = ["종목코드", "종목명", "결산월", "액면가", "자본금",
				"상장주식", "신용비율", "연중최고", "연중최저", "시가총액",
				"시가총액비중", "외인소진률", "대용가", "PER", "EPS",
				"ROE", "PBR", "EV", "BPS", "매출액",
				"영업이익", "당기순이익", "D250최고", "D250최저", "시가",
				"고가", "저가", "상한가", "하한가", "기준가",
				"예상체결가", "예상체결수량", "D250최고가일", "D250최고가대비율", "D250최저가일",
				"D250최저가대비율", "현재가", "대비기호", "전일대비", "등락율",
				"거래량", "거래대비", "액면가단위", "유통주식", "유통비율", "입력일"]
kospi_list = []
kosdaq_list = []

# connect to db
stock_con = sqlite3.connect(dbPath + stockDb)
stock_cur = stock_con.cursor()

# DEBUG:0 (disabled) or DEBUG:1 (enabled)
DEBUG = 1
def debug_print(x):
	if DEBUG == 0:
		return
	print(x)

def get_jongmokInfo(table_name):
	jongmok_sql = "SELECT * FROM " + table_name + ";"
	#debug_print(jongmok_sql)
	stock_cur.execute(jongmok_sql)
	records = stock_cur.fetchall()
	return records

def get_quarterly_perf(code, quarter):
	search_sql = "SELECT * FROM " + qp_table + \
				" WHERE " + \
				qp_field[0] + "='" + code + "'" + \
				" AND " + \
				qp_field[1] + "='" + quarter + "';"
	stock_cur.execute(search_sql)
	result = stock_cur.fetchall()
	if len(result) == 0:
		return None
	return result

#################################################################
#
# You can check your algorithm by modifying this function
# With current code, the dataframe format will be like this.
# --------------------------------------------------------------
# |종목코드|종목명|시가총액|PER|EPS|ROE|PBR|
#        전년동기매출액|전년동기영업이익|직전분기매출액|직전분기영업이익|
#        분기매출액|분기영업이익|멀티플|
# --------------------------------------------------------------
def getQPField(record, field_name):
	if record[0][qp_field.index(field_name)] == "-":
		return -1
	return float(record[0][qp_field.index(field_name)])

def isValuable(qpr0, qpp0, qpr1, qpp1, qpr, qpp, mul):
	# 전년 동기보다 매출액, 영업이익이 늘었는가?
	if qpr0 > qpr or qpp0 > qpp:
		return False
	# 직전분기보다 매출액, 영업이익이 늘었는가?
	if qpr1 > qpr or qpp1 > qpp:
		return False
	# multiple이 10이하인가?
	if mul > 10:
		return False
	return True

def search_company():
	kospi_list = get_jongmokInfo("kospi")
	kosdaq_list = get_jongmokInfo("kosdaq")
	all_company = kospi_list + kosdaq_list
	if len(all_company) == 0:
		print("ERROR: kospi kosdaq company record is 0")
		return
	# 현분기, 전년동기, 직전분기 hardcoding
	quarter = "2020.06"
	py_quarter = "2019.06"
	pr_quarter = "2020.03"
	rows = []
	cols = ["종목코드", "종목명", "시가총액", "PER", "EPS", "ROE", "PBR"] + \
		[py_quarter+" 매출액", py_quarter+" 영업이익"] + \
		[pr_quarter+" 매출액", pr_quarter+" 영업이익"] + \
		[quarter+" 매출액", quarter+" 영업이익", "멀티플"]
	for i in range(len(all_company)):
		code = all_company[i][codeDataName.index("종목코드")]
		if code == '':
			continue
		name = all_company[i][codeDataName.index("종목명")]
		stsum = float(all_company[i][codeDataName.index("시가총액")])
		per = all_company[i][codeDataName.index("PER")]
		eps = all_company[i][codeDataName.index("EPS")]
		roe = all_company[i][codeDataName.index("ROE")]
		pbr = all_company[i][codeDataName.index("PBR")]

		qp = get_quarterly_perf(code, quarter)
		if qp == None:
			continue
		qp_revenue = getQPField(qp, "매출액")
		if qp_revenue == -1:
			continue
		qp_profit = getQPField(qp, "영업이익")
		if qp_profit == -1:
			continue

		qp0 = get_quarterly_perf(code, py_quarter)
		if qp0 == None:
			continue
		qp0_revenue = getQPField(qp0, "매출액")
		if qp0_revenue == -1:
			continue
		qp0_profit = getQPField(qp0, "영업이익")
		if qp0_profit == -1:
			continue

		qp1 = get_quarterly_perf(code, pr_quarter)
		if qp1 == None:
			continue
		qp1_revenue = getQPField(qp1, "매출액")
		if qp1_revenue == -1:
			continue
		qp1_profit = getQPField(qp1, "영업이익")
		if qp1_profit == -1:
			continue

		# check if company is valuable
		multiple = stsum / (4 * qp_profit)
		if isValuable(qp0_revenue, qp0_profit, \
			qp1_revenue, qp1_profit, qp_revenue, qp_profit, multiple) == False:
			continue
		# create record array
		row = [code, name, stsum, per, eps, roe, pbr] + \
			[qp0_revenue, qp0_profit] + \
			[qp1_revenue, qp1_profit] + \
			[qp_revenue, qp_profit, multiple]
		rows.append(row)
	df = DataFrame(rows, columns=cols)
	debug_print(df)
	today = datetime.today().strftime("%Y-%m-%d")
	xls_filename = "company_" + today + ".xlsx"
	df.to_excel(excel_writer=xls_filename)

if __name__ == "__main__":
	search_company()