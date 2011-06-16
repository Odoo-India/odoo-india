import pooler
import sys
from osv import osv
import ledgers
import stock
import employee



class migrator():
	def getPoolObj(self, cr):
		return pooler.get_pool(cr.dbname)

	def getAccountObj(self, pool):
		account = pool.get('account.account')
		acc_type = pool.get('account.account.type')
		return account, acc_type

	def getStockObj(self, pool):
		uom = pool.get('product.uom')
		prod = pool.get('product.product')
		prodCat = pool.get('product.category')
		currency = pool.get('res.currency')
		return uom, prod, prodCat, currency

	def getStockLocationObj(self, pool):
		return pool.get('stock.location')
	
	def getEmployeeObj(self,pool):
		return pool.get('hr.employee')

	def insertData(self, cr, uid, com, tallyData):
		a = tallyData
	
		pool = self.getPoolObj(cr)
		account, acc_type = self.getAccountObj(pool)
		uomObj, prodObj, prodCatObj, currencyObj = self.getStockObj(pool)
		godownObj = self.getStockLocationObj(pool)
		empObj = self.getEmployeeObj(pool)
	
		if a.has_key('TALLYMESSAGE'):
			l = len(a['TALLYMESSAGE'])
			dic = {}
		
			if l<=0:
				pass
			
			elif l<2:  #for single record [TALLYMESSAGE] is dictionary.
				k = a['TALLYMESSAGE'].keys()[0]
				dic = a['TALLYMESSAGE'][k]
				if (k=='GROUP' or k=='LEDGER'):
					if dic.has_key('NAME') and dic['NAME']:
						obj_ledgers = ledgers.ledgers()
						obj_ledgers.insertRecords(cr, uid, dic, com, account, acc_type)
				elif (k=='UNIT'):
					obj_stock = stock.stock()
					obj_stock.insertUnits(cr, uid, uomObj, dic)
				elif (k=='STOCKGROUP'):
					obj_stock = stock.stock()
					obj_stock.insertStockGroups(cr, uid, prodCatObj, dic)
				elif (k=='STOCKITEM'):
					obj_stock = stock.stock()
					obj_stock.insertStockItems(cr, uid, prodObj, uomObj, prodCatObj, dic, com)
				elif (k=='CURRENCY'):
					obj_stock = stock.stock()
					obj_stock.insertCurrencies(cr, uid, currencyObj, dic, com)
				elif (k=='GODOWN'):
					obj_stock = stock.stock()
					obj_stock.insertGodowns(cr, uid, godownObj, dic, com)
				elif (k=='COSTCENTRE'):
					obj_employee = employee.employee()
					obj_employee.insertEmployees(cr, uid, empObj, dic, com)
			
			else:    #for multiple records [TALLYMESSAGE] is list of dictionaries.
				for i in a['TALLYMESSAGE']:
					k = i.keys()[0]
					dic = i[k]
					if (k=='GROUP' or k=='LEDGER'):		
						if dic.has_key('NAME') and dic['NAME']:
							obj_ledgers = ledgers.ledgers()
							obj_ledgers.insertRecords(cr, uid, dic, com, account, acc_type)
					elif (k=='UNIT'):
						obj_stock = stock.stock()
						obj_stock.insertUnits(cr, uid, uomObj, dic)
					elif (k=='STOCKGROUP'):
						obj_stock = stock.stock()
						obj_stock.insertStockGroups(cr, uid, prodCatObj, dic)
					elif (k=='STOCKITEM'):
						obj_stock = stock.stock()
						obj_stock.insertStockItems(cr, uid, prodObj, uomObj, prodCatObj, dic, com)
					elif (k=='CURRENCY'):
						obj_stock = stock.stock()
						obj_stock.insertCurrencies(cr, uid, currencyObj, dic, com)
					elif (k=='GODOWN'):
						obj_stock = stock.stock()
						obj_stock.insertGodowns(cr, uid, godownObj, dic, com)
					elif (k=='COSTCENTRE'):
						obj_employee = employee.employee()
						obj_employee.insertEmployees(cr, uid, empObj, dic, com)

