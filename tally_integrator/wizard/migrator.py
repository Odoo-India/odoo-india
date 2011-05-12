from psycopg2 import IntegrityError
from osv import osv
import string
import pooler

code = 0
	
def getAccountObj(cr):
	pool = pooler.get_pool(cr.dbname)
	account = pool.get('account.account')
	acc_type = pool.get('account.account.type')
	return account, acc_type


def insertRecords(cr, uid, dic, com, account, acc_type):
	global code 
	
	if dic.has_key('PARENT') and dic['PARENT']:
		domain = [('name','=',dic['PARENT']),('company_id','=',com.id)]
		
	else:
		domain = [('name','=',com.name)]
		
		
		
	code += 1		
	parent_id = account.search(cr, uid, domain)
	if not parent_id:
		#raise osv.except_osv(('Error !'), ('Specified Company not Found in account.account records!!!'))
		data = {'name':com.name, 'code':string.upper(com.name[0:3]), 'type':'view', 'currency_mode':'current', 'user_type':1, 'company_id':com.id}
		try:
			parent_id = account.create(cr, uid, data)
		except:
			raise osv.except_osv(('Error !'), ('Company code already exist please use another company name.'))
	else:
		
		obj = account.browse(cr, uid, parent_id[0])
		p_code = obj.code
		typ = 0
		usr_typ = 0
		
		if dic.has_key('PARENT') and dic['PARENT']:
			usr_typ = obj.user_type.id
			typ = obj.type
		else:
			if dic.has_key('ISREVENUE') and dic.has_key('ISDEEMEDPOSITIVE'):
				if dic['ISREVENUE']=='Yes' and dic['ISDEEMEDPOSITIVE']=='Yes':
					usr_typ = acc_type.search(cr, uid, [('code','=','expense')])
					typ = 'other'
				elif dic['ISREVENUE']=='Yes':
					usr_typ = acc_type.search(cr, uid, [('code','=','income')])
					typ = 'other'
				elif dic['ISDEEMEDPOSITIVE']=='Yes':
					usr_typ = acc_type.search(cr, uid, [('code','=','asset')])
					typ = 'receivable'
				elif dic['ISREVENUE']=='No' and dic['ISDEEMEDPOSITIVE']=='No':
					usr_typ = acc_type.search(cr, uid, [('code','=','liability')])
					typ = 'payable'
				usr_typ = usr_typ[0]
			else: 
				usr_typ = obj.user_type.id
				typ = obj.type
		
		data = {'name':dic['NAME'], 'code':p_code + str(code), 'type':typ, 'parent_id':parent_id[0], 'currency_mode':'current', 'user_type':usr_typ, 'company_id':com.id}

		
		try:
			p_id = account.create(cr, uid, data)

		except IntegrityError, e:
			code += 50
			raise osv.except_osv(('Unique Code Constraint Error'), ('Please Retry the Data Migration.'))


		
def insertData(cr, uid, com, tallyData):
	global code
	a = tallyData
	account, acc_type = getAccountObj(cr)
	if a.has_key('TALLYMESSAGE'):
		l = len(a['TALLYMESSAGE'])
		dic = {}
		
		if l<=0:
			print "Sorry! There are no records."
			
		elif l<2:  #for single record [TALLYMESSAGE] is dictionary.
			k = a['TALLYMESSAGE'].keys()[0]
			if (k=='GROUP' or k=='LEDGER'):
				dic = a['TALLYMESSAGE'][k]
				if dic.has_key('NAME') and dic['NAME']:
					domain = [('name','=',dic['NAME']),('company_id','=',com.id)]
					search_id = account.search(cr, uid, domain)
					if not search_id:
						insertRecords(cr, uid, dic, com, account, acc_type)
					else:
						code += 1
			
		else:    #for multiple records [TALLYMESSAGE] is list of dictionaries.
			for i in a['TALLYMESSAGE']:
				k = i.keys()[0]
				if (k=='GROUP' or k=='LEDGER'):
					dic = i[k]		
					if dic.has_key('NAME') and dic['NAME']:
						domain = [('name','=',dic['NAME']),('company_id','=',com.id)]
						search_id = account.search(cr, uid, domain)
						if not search_id:
							insertRecords(cr, uid, dic, com, account, acc_type)
						else:
							code += 1
				
