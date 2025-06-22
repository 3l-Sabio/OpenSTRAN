import os
import sqlite3

class QuerySteelDb():
	def __init__(self):
		self.path = os.path.join(os.getcwd(),'Steel_Sections.db')
		self.table = 'AISC_SSDB_V15'
		self.headers = [
		'Type', 'EDI_Std_Nomenclature', 'AISC_Manual_Label', 'T_F', 'W', 'A', 'd', 'ddet',
		'Ht', 'h1', 'OD', 'bf', 'bfdet', 'B1', 'b2', 'ID', 'tw', 'twdet', 'twdet_over_2',
		'tf', 'tfdet', 't1', 'tnom', 'tdes', 'kdes', 'kdet', 'k1', 'x', 'y', 'eo', 'xp', 
		'yp', 'bf_over_2tf', 'b_over_t', 'b_over_tdes', 'h_over_tw', 'h_over_tdes', 'D_over_t',
		'Ix', 'Zx', 'Sx', 'rx', 'Iy', 'Zy', 'Sy', 'ry', 'Iz', 'rz', 'Sz', 'J', 'Cw', 'C', 'Wno',
		'Sw1', 'Sw2', 'Sw3', 'Qf', 'Qw', 'ro', 'H', 'tana', 'Iw', 'zA', 'zB', 'zC', 'wA', 'wB',
		'wC', 'SwA', 'SwB', 'SwC', 'SzA', 'SzB', 'SzC', 'rts', 'ho', 'PA', 'PA2', 'PB', 'PC',
		'PD', 'T', 'WGi', 'WGo'
		]
		self.units = [
		'[-]', '[-]', '[-]', '[-]', '[lb/ft]', '[in^2]', '[in]', '[in]', '[in]', '[in]', '[in]',
		'[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]',
		'[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[-]',
		'[-]', '[-]', '[-]', '[-]', '[-]', '[in^4]', '[in^3]', '[in^3]', '[in]', '[in^4]', '[in^3]',
		'[in^3]', '[in]', '[in^4]', '[in]', '[in^3]', '[in^4]', '[in^6]', '[in^3]', '[in^2]',
		'[in^4]', '[in^4]', '[in^4]', '[in^3]', '[in^3]', '[in]', '[-]', '[-]', '[in^4]', '[in]',
		'[in]', '[in]', '[in]', '[in]', '[in]', '[in^3]', '[in^3]', '[in^3]', '[in^3]', '[in^3]',
		'[in^3]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]', '[in]','[in]'
		]
		self.records = []

	def Connect(self):
		self.connection = sqlite3.connect(self.path)
		self.cursor = self.connection.cursor()

	def Disconnect(self):
		self.connection.commit()
		self.connection.close()

	def FormatRecords(self, records, Query):
		if Query in ['Get_AISC_Manual_Labels','Get_AISC_Manual_Types']:
			for i, record in enumerate(records):
				records[i] = record[0]
			return(records)
		elif Query == 'Get_Section_Properties':
			return({k: [v,u] for k, v, u in zip(self.headers, records[0], self.units) if v != None})


	def ReturnRecords(self, records, Query):
		if records == None:
			return('No Records Found')
		else:
			return(self.FormatRecords(records, Query))

	def Get_AISC_Manual_Types(self):
		self.Connect()
		self.sql_select_query = """SELECT DISTINCT Type FROM {Table}""".format(Table=self.table)
		self.cursor.execute(self.sql_select_query)
		self.records = self.cursor.fetchall()
		return(self.ReturnRecords(self.records, 'Get_AISC_Manual_Types'))
		self.Disconnect()

	def Get_AISC_Manual_Labels(self, Type):
		self.Connect()
		self.sql_select_query = """SELECT AISC_Manual_Label FROM {Table} WHERE Type = ?""".format(Table=self.table)
		self.cursor.execute(self.sql_select_query, (Type,))
		self.records = self.cursor.fetchall()
		return(self.ReturnRecords(self.records, 'Get_AISC_Manual_Labels'))
		self.Disconnect()

	def Get_Section_Properties(self, AISC_Manual_Label):
		self.Connect()
		self.sql_select_query = """SELECT * FROM {Table} WHERE AISC_Manual_Label = ?""".format(Table=self.table)
		self.cursor.execute(self.sql_select_query, (AISC_Manual_Label,))
		self.records = self.cursor.fetchall()
		return(self.ReturnRecords(self.records, 'Get_Section_Properties'))
		self.Disconnect()

	def Get_Shapes(self, Type, Label):
		self.Connect()
		self.sql_select_query = """SELECT AIC_Manual_Label FROM {Table} WHERE Type = ? AND AISC_Manual_Label LIKE ?""".format(Table=self.table)
		self.cursor.execute(self.sql_select_query, (Type,), ('%'+Label+'%',))
		self.records = self.cursor.fetchall()
		return(self.ReturnRectords(self.records, 'Get_Shapes'))
		self.Disconnect()
