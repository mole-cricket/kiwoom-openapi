#############################################################
# Quarterly Performance Update Script using Naver Finance
#############################################################
# How to run
# ex> q_perf_update.py 2020.06
#
#
#############################################################

import pandas as pd
import requests
import sqlite3

NF_URL = "https://finance.naver.com/item/main.nhn?code="

dbPath = "c:/StockDB/"
stockDb = "myStock.db"

# quarterly performance table info
qp_table = "q_perf_report"
qp_field = [ "종목코드", "분기", "매출액", "영업이익", "당기순이익",
			 "영업이익률", "순이익률", "ROE", "부채비율", "당좌비율",
			 "유보율", "EPS", "PER", "BPS", "PBR" ]
qp_type = [ "text", "text", "int", "int", "int",
			"real", "real", "real", "real", "real",
			"real", "int", "real", "int", "real" ]

# Naver's Quarterly Performance Actual Key in Dictionary
qp_name = [ "종목코드", "분기", "매출액", "영업이익", "당기순이익",
			 "영업이익률", "순이익률", "ROE(지배주주)", "부채비율", "당좌비율",
			 "유보율", "EPS(원)", "PER(배)", "BPS(원)", "PBR(배)" ]

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

# create qp_table field for check_n_create_QPTable()
def create_QPField():
	primary = "PRIMARY KEY("
	field = "("
	for i in range(len(qp_field)):
		field = field + qp_field[i] + " " + qp_type[i]
		if i == 0:
			field = field + " NOT NULL, "
			primary = primary + qp_field[i] + ", "
		elif i == 1:
			field = field + " NOT NULL, "
			primary = primary + qp_field[i] + ") "
		elif i == len(qp_field) - 1:
			field = field + ", " + primary + ");"
		else:
			field = field + ", "
	return field

# check and create quarterly performance table if not exist
def check_n_create_QPTable():
	stock_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + qp_table + "'")
	exist = stock_cur.fetchall()
	if len(exist) == 0:
		# create tables
		field = create_QPField()
		create_qp_tbl_sql = "CREATE TABLE " + qp_table + field
		debug_print(create_qp_tbl_sql)
		stock_cur.execute(create_qp_tbl_sql)
		stock_con.commit()
		debug_print("분기실적 테이블 생성: " + qp_table)
	else:
		debug_print("분기실적 테이블 존재: " + qp_table)

def get_jongmokCode(table_name):
	jongmok_sql = "SELECT * FROM " + table_name + ";"
	debug_print(jongmok_sql)
	stock_cur.execute(jongmok_sql)
	records = stock_cur.fetchall()
	code_list = []
	for i in range(len(records)):
		if records[i][0] != '':
			code_list.append(records[i][0])
	debug_print("DB 종목코드 리스트 리턴: " + str(len(code_list)))
	return code_list

def get_jongmokName(table, code):
	name_sql = "SELECT 종목명 FROM " + table + " WHERE 종목코드='" + code +"';"
	stock_cur.execute(name_sql)
	records = stock_cur.fetchall()
	if len(records) == 0:
		return ""
	return records[0][0]

def get_jongmokNameByCode(code):
	name = get_jongmokName("kospi", code)
	if name == "":
		name = get_jongmokName("kosdaq", code)
	return name

def initDB():
	global kospi_list
	global kosdaq_list

	# check & create quarterly performance table
	check_n_create_QPTable()
	kospi_list = get_jongmokCode("kospi")
	debug_print("---------------kospi--------------")
	debug_print("| record count: " + str(len(kospi_list)))
	debug_print("---------------kospi--------------")
	debug_print(kospi_list)
	kosdaq_list = get_jongmokCode("kosdaq")
	debug_print("---------------kosdaq--------------")
	debug_print("| record count: " + str(len(kosdaq_list)))
	debug_print("---------------kosdaq--------------")
	debug_print(kosdaq_list)

def input_year_quarter():
	print("가져올 분기를 입력하세요. 예: 2020.06")
	quarter_str = input()
	if len(quarter_str) != 7:
		print("ERROR: 잘못된 포맷의 입력입니다.")
		return ""
	return quarter_str

def get_quarter():
	quarter = ""
	while quarter == "":
		quarter = input_year_quarter()
	return quarter

#######################################################################
# This is test function to check all the layout of html
# only for development. If there is any problem in parsing data,
# use this function and adapt script to new page layout and
# modify get_n_parse_jongmok()
def test_get_n_parse_jongmok(jongmok_code, quarter):
	nf_resp = requests.get(NF_URL + jongmok_code)
	df = pd.read_html(nf_resp.text)[5]
	df = df.append(pd.read_html(nf_resp.text)[6])
	df = df.append(pd.read_html(nf_resp.text)[7])
	df = df.append(pd.read_html(nf_resp.text)[8])
	df = df.append(pd.read_html(nf_resp.text)[9])
	print(df)
	print(df.iloc[0][1])

	financial_stmt = pd.read_html(nf_resp.text)[3]
	financial_stmt.set_index(('주요재무정보', '주요재무정보', '주요재무정보'), inplace=True)
	financial_stmt.index.rename('주요재무정보', inplace=True)
	financial_stmt.columns = financial_stmt.columns.droplevel(2)
	fs_dict = financial_stmt.to_dict()
	print(fs_dict)
	print(fs_dict[('최근 분기 실적', quarter)]['매출액'])
	print(fs_dict[('최근 분기 실적', quarter)]['영업이익'])
	print(fs_dict[('최근 분기 실적', quarter)]['당기순이익'])

def get_n_parse_jongmok(jongmok_code, quarter):
	nf_resp = requests.get(NF_URL + jongmok_code)
	financial_stmt = pd.read_html(nf_resp.text)[3]
	# NOTE: 지수 종목은 재무정보가 없으므로 예외 처리
	if (('주요재무정보', '주요재무정보', '주요재무정보') in financial_stmt) == False:
		return None
	financial_stmt.set_index(('주요재무정보', '주요재무정보', '주요재무정보'), inplace=True)
	financial_stmt.index.rename('주요재무정보', inplace=True)
	financial_stmt.columns = financial_stmt.columns.droplevel(2)
	fs_dict = financial_stmt.to_dict()
	#debug_print(fs_dict)

	# NOTE: 간혹 가져온 딕셔너리 데이타에 키값이 잘못 입력되어 있는 경우가 있다.
	# 3분기 데이타가 2020.08로 되어있다든지. 이런 경우 한달 전 값을 다시 시도해본다.
	input_qt = quarter
	if (('최근 분기 실적', input_qt) in fs_dict) == False:
		print("ERROR: 최근 분기 실적 " + input_qt + " 없음")
		alt_qt = { "03":"02", "06":"05", "09":"08", "12":"11"}
		input_qt = input_qt[:-2] + alt_qt[input_qt[-2:]]
		print("RETRY: 최근 분기 실적 " + input_qt + " 재시도")
		# NOTE: 새로 상장된 회사의 경우에 분기실적이 존재하지 않으므로 이렇게도 안되면
		# 그냥 스킵한다.
		if (('최근 분기 실적', input_qt) in fs_dict) == False:
			return None
	qp = fs_dict[('최근 분기 실적', input_qt)]
	debug_print(fs_dict[('최근 분기 실적', input_qt)])

	parsed_data = [ jongmok_code, quarter ]
	for i in range(2, len(qp_name)):
		debug_print(qp_name[i] + ": " + str(fs_dict[('최근 분기 실적', input_qt)][qp_name[i]]))
		parsed_data.append( str(fs_dict[('최근 분기 실적', input_qt)][qp_name[i]]) )
	debug_print(parsed_data)
	return parsed_data

def exist_record(code, quarter):
	search_sql = "SELECT * FROM " + qp_table + \
				" WHERE " + \
				qp_field[0] + "='" + code + "'" + \
				" AND " + \
				qp_field[1] + "='" + quarter + "';"
	stock_cur.execute(search_sql)
	exist = stock_cur.fetchall()
	if len(exist) == 0:
		return 0
	return 1

def insert_record(record):
	values = "VALUES ("
	for i in range(len(record)):
		values = values + "'" + record[i] + "'"
		if i == len(record) - 1:
			values = values + ");"
		else:
			values = values + ", "

	insert_sql = "INSERT INTO " + qp_table + " " + values
	debug_print(insert_sql)
	stock_cur.execute(insert_sql)
	stock_con.commit()

def parse_n_store_all_jongmok(quarter):
	global kospi_list
	global kosdaq_list
	all_jongmok = kospi_list + kosdaq_list
	debug_print("가져올 종목 갯수: " + str(len(all_jongmok)) + "개")
	count = 0
	for code in all_jongmok:
		name = get_jongmokNameByCode(code)
		# check
		if exist_record(code, quarter) == 1:
			debug_print("존재> 종목코드: " + code + ", 종목명: " + name + ", 분기: " + quarter)
			continue
		count = count + 1
		debug_print("신규> No: " + str(count) + ", 종목코드: " + code + \
					", 종목명: " + name + ", 분기: " + quarter)
		# get & parse
		data = get_n_parse_jongmok(code, quarter)
		if data is None:
			print("INFO: Skip " + code + " (" + name + ")")
			continue
		# store
		insert_record(data)
	debug_print("Total: " + str(count) + "개 레코드 입력")

if __name__ == "__main__":
	initDB()
	quarter = get_quarter()
	parse_n_store_all_jongmok(quarter)