# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import pooler
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError
import string
from osv import osv

class voucher():	

	poolObj = ''
	voucherObj = ''
	acctObj = ''
	partnerObj = ''
	jrObj = ''

	def __init__(self, cr):
		self.poolObj = pooler.get_pool(cr.dbname)
		self.voucherObj = self.poolObj.get('account.voucher')
		self.acctObj = self.poolObj.get('account.account')
		self.partnerObj = self.poolObj.get('res.partner')
		self.jrObj = self.poolObj.get('account.journal')
		
	# Creates 'fiscal year' and its 12 'periods'
	def createFY(self, cr, uid, dt, company):
		fiscalYrObj = self.poolObj.get('account.fiscalyear')
		
		yr = int(dt[:4])
		data = {'code':'FY'+dt[:4], 'name':'Fiscal Year '+dt[:4]+' '+company.name, 'company_id':company.id, 'date_start':datetime(yr,01,01), 'date_stop':datetime(yr,12,31)}
		
		fy_id = fiscalYrObj.create(cr, uid, data)
		
		fy = fiscalYrObj.browse(cr, uid, fy_id)

		ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
		while ds.strftime('%Y-%m-%d')<fy.date_stop:
		    de = ds + relativedelta(months=1, days=-1)

		    if de.strftime('%Y-%m-%d')>fy.date_stop:
		        de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

		    self.poolObj.get('account.period').create(cr, uid, {
		        'name': ds.strftime('%m/%Y'),
		        'code': ds.strftime('%m/%Y'),
		        'date_start': ds.strftime('%Y-%m-%d'),
		        'date_stop': de.strftime('%Y-%m-%d'),
		        'fiscalyear_id': fy.id,
		    })
		    ds = ds + relativedelta(months=1)
		return fy_id
	
	def createAccountMoveLine(self, cr, uid, dic, move_id, period_id, journal_id, VTYPE, com):
		vtype = VTYPE
		if vtype == 'Sale' or vtype == 'Purchase':
			
			if dic.has_key('LEDGERENTRIES.LIST') and dic['LEDGERENTRIES.LIST']:
				
				i = dic['LEDGERENTRIES.LIST']
			
				amount = float(i['AMOUNT'])
				if amount>0:
					credit = amount
				else:
					debit = amount * (-1)
			
				name = i[0]['LEDGERNAME']
			
				domain = [('name','=',name),('company_id','=',com.id)]
				sid = self.acctObj.search(cr,uid ,domain)
				Object = self.acctObj.browse(cr, uid, sid[0])
				if Object.type == 'view' or Object.type == 'closed':
					return True
				
				data = {'name':name, 'debit':debit, 'credit':credit, 'account_id':sid[0], 'move_id':move_id, 'period_id':period_id, 'journal_id':journal_id}
				accMoveLineObj = self.poolObj.get('account.move.line')
				try:
					accMoveLineObj.create(cr, uid, data)
				except Exception, e:
					raise osv.except_osv(('Move Line Creation Error!!!'), str(e))
					
		else: #if vtype == 'Payment' or vtype == 'Receipt':
			
			if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']:
				entries = dic['ALLLEDGERENTRIES.LIST']
				for i in entries:
				
					credit = 0
					debit = 0
			
					name = i['LEDGERNAME']
			
					domain = [('name','=',name),('company_id','=',com.id)]
					sid = self.acctObj.search(cr,uid ,domain)
					Object = self.acctObj.browse(cr, uid, sid[0])
					if Object.type == 'view' or Object.type == 'closed':
						return True
				
					accMoveLineObj = self.poolObj.get('account.move.line')

					amount = float(i['AMOUNT'])
					if amount>0:
						credit = amount
					else:
						debit = amount * (-1)
					
					data = {'name':name, 'debit':debit, 'credit':credit, 'account_id':sid[0], 'move_id':move_id, 'period_id':period_id, 'journal_id':journal_id}
					
					try:
						accMoveLineObj.create(cr, uid, data)
					except Exception, e:
						raise osv.except_osv(('Move Line Creation Error!!!'), str(e))
					
		return True
	
	def createAccountMove(self, cr, uid, dic, period_id, VTYPE, com):
		
		if dic.has_key('DATE') and dic['DATE']:
			date = dic['DATE']
			
		narration = ''
		if dic.has_key('NARRATION') and dic['NARRATION']:
			narration = dic['NARRATION']
		
		#searching for the 'Company Account'
		acc_id = self.acctObj.search(cr, uid, [('name','=',com.name),('company_id','=',com.id)])
		
		#Creating 'General' Journal for Indirect Incomes/Expenses.
		journalObj = self.poolObj.get('account.journal')
		journalName = 'General Journal'+" - ("+com.name+")"

		#assigning 'Company Account' to 'default_debit_account_id' and 'default_credit_account_id' for the 'General'
		GeneralJournalData = {'name':journalName, 'code':'GEN-'+com.name[0], 'type':'general', 'default_debit_account_id':acc_id[0], 'default_credit_account_id':acc_id[0], 'company_id':com.id, 'view_id':3}
		journal_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])
		if journal_id:
			journalObj.write(cr, uid, journal_id, GeneralJournalData)
			journal_id = journal_id[0]
		else:
			journal_id = journalObj.create(cr, uid, GeneralJournalData)

		data = {'period_id':period_id, 'journal_id':journal_id, 'date':date, 'narration':narration}

		#creating entries in 'account.move'		
		move_id = accMoveObj = self.poolObj.get('account.move').create(cr, uid, data)

		#creating entries for 'account.move.line'
		self.createAccountMoveLine(cr, uid, dic, move_id, period_id, journal_id, VTYPE, com)
		
		return True
	
	def createAccountVoucherLine(self, cr, uid, dic, com, voucher_id, vtype):
		
		if vtype == 'Sale' or vtype == 'Purchase':
			
			if dic.has_key('LEDGERENTRIES.LIST') and dic['LEDGERENTRIES.LIST']:
				
				i = dic['LEDGERENTRIES.LIST']
				if float(i['AMOUNT'])<0:
					typ = 'cr'
					i['AMOUNT'] = float(i['AMOUNT']) * (-1)
				else:
					typ = 'dr'
				
				if vtype == 'Sale':	
					name = 'Sales Accounts'
				elif vtype == 'Purchase':
					name = 'Purchase Accounts'
				
				domain = [('name','=',name),('company_id','=',com.id)]
				sid = self.acctObj.search(cr,uid ,domain)
				
				data = {'voucher_id':voucher_id, 'name':'', 'account_id':sid[0], 'amount':i['AMOUNT'], 'type':typ}
				accVhrLineObj = self.poolObj.get('account.voucher.line')
				try:
					accVhrLineObj.create(cr, uid, data)
				except Exception, e:
					raise osv.except_osv(('Voucher Line Creation Error!!!'), str(e))
			
			if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']:
				entries = dic['ALLLEDGERENTRIES.LIST']
				
				for i in entries:
				
					if float(i['AMOUNT'])>0:
						typ = 'cr'
						name = i['LEDGERNAME']
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)
						if not sid:
							name = i['LEDGERNAME']+' (Creditors)'
							domain = [('name','=',name),('company_id','=',com.id)]
							sid = self.acctObj.search(cr,uid ,domain)
					else:
						typ = 'dr'
						i['AMOUNT'] = float(i['AMOUNT']) * (-1)
						name = i['LEDGERNAME']
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)
						if not sid:
							name = i['LEDGERNAME']+' (Debtors)'
							domain = [('name','=',name),('company_id','=',com.id)]
							sid = self.acctObj.search(cr,uid ,domain)

					data = {'voucher_id':voucher_id, 'name':'', 'account_id':sid[0], 'amount':i['AMOUNT'], 'type':typ}
					accVhrLineObj = self.poolObj.get('account.voucher.line')
					try:
						accVhrLineObj.create(cr, uid, data)
					except Exception, e:
						raise osv.except_osv(('Voucher Line Creation Error!!!'), str(e))
					
		elif vtype == 'Payment' or vtype == 'Receipt':
			
			if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']:
				entries = dic['ALLLEDGERENTRIES.LIST']
				length = len(entries)
				#for i in entries:
				i = entries[length - 1]
				if float(i['AMOUNT'])>0:
					typ = 'cr'
					name = i['LEDGERNAME']
					domain = [('name','=',name),('company_id','=',com.id)]
					sid = self.acctObj.search(cr,uid ,domain)
					if not sid:
						name = i['LEDGERNAME']+' (Creditors)'
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)
				else:
					typ = 'dr'
					i['AMOUNT'] = float(i['AMOUNT']) * (-1)
					name = i['LEDGERNAME']
					domain = [('name','=',name),('company_id','=',com.id)]
					sid = self.acctObj.search(cr,uid ,domain)
					if not sid:
						name = i['LEDGERNAME']+' (Debtors)'
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)

				data = {'voucher_id':voucher_id, 'name':'', 'account_id':sid[0], 'amount':i['AMOUNT'], 'type':typ}
				accVhrLineObj = self.poolObj.get('account.voucher.line')
				try:
					accVhrLineObj.create(cr, uid, data)
				except Exception, e:
					raise osv.except_osv(('Voucher Line Creation Error!!!'), str(e))
				
		else:
			vtype = 'Receipt'
			if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']:
				entries = dic['ALLLEDGERENTRIES.LIST']
				
				for i in entries:
				
					if float(i['AMOUNT'])>0:
						typ = 'cr'
						name = i['LEDGERNAME']
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)
						if not sid:
							name = i['LEDGERNAME']+' (Creditors)'
							domain = [('name','=',name),('company_id','=',com.id)]
							sid = self.acctObj.search(cr,uid ,domain)
					else:
						typ = 'dr'
						i['AMOUNT'] = float(i['AMOUNT']) * (-1)
						name = i['LEDGERNAME']
						domain = [('name','=',name),('company_id','=',com.id)]
						sid = self.acctObj.search(cr,uid ,domain)
						if not sid:
							name = i['LEDGERNAME']+' (Debtors)'
							domain = [('name','=',name),('company_id','=',com.id)]
							sid = self.acctObj.search(cr,uid ,domain)

					data = {'voucher_id':voucher_id, 'name':'', 'account_id':sid[0], 'amount':i['AMOUNT'], 'type':typ}
					accVhrLineObj = self.poolObj.get('account.voucher.line')
					try:
						accVhrLineObj.create(cr, uid, data)
					except Exception, e:
						raise osv.except_osv(('Voucher Line Creation Error!!!'), str(e))
	
		return True
	
	def insertVouchers(self, cr, uid, dic, com):
		
		vtype = ''
		DATE = ''
		NARRATION = ''
		ACC_ID = ''
		JR_ID = ''

		#'Date' is used to create 'fiscal year' and its related 'periods'
		if dic.has_key('DATE') and dic['DATE']: #for date and fiscal year & periods
			DATE = dic['DATE']
			fiscalYrObj = self.poolObj.get('account.fiscalyear')
			
			domain = [('code','=','FY'+DATE[:4]),('company_id','=',com.id)]
			fy_id = fiscalYrObj.search(cr, uid, domain)

			#If fiscal year is not found then create Fiscal Year and its related periods.
			if not fy_id:
				fy_id = self.createFY(cr, uid, DATE, com)
				#searching the period from the specified date.
				period_id = self.poolObj.get('account.period').search(cr, uid, [('code','=',DATE[4:6]+'/'+DATE[:4]),('fiscalyear_id','=',fy_id)])
			#searching the period from the specified date.
			else:
				period_id = self.poolObj.get('account.period').search(cr, uid, [('code','=',DATE[4:6]+'/'+DATE[:4]),('fiscalyear_id','=',fy_id[0])])
		
		# deciding partner name for the 'Accounting Voucher'.
		#if 'PARTYLEDGERNAME' is there then search for the partner.
		if dic.has_key('PARTYLEDGERNAME') and dic['PARTYLEDGERNAME']: 
			partner_id = self.partnerObj.search(cr, uid, [('name','=',dic['PARTYLEDGERNAME']),('company_id','=',com.id)])
			if not partner_id:
				partner_id = self.partnerObj.search(cr, uid, [('name','=',com.name),('company_id','=',com.id)])
			part_obj = self.partnerObj.browse(cr, uid, partner_id[0])
		#else search for the 'Company Partner'
		else:
			partner_id = self.partnerObj.search(cr, uid, [('name','=',com.name),('company_id','=',com.id)])
			part_obj = self.partnerObj.browse(cr, uid, partner_id[0])
		
		# deciding 'voucher type' for the 'Accounting Voucher'
		#for journal and account selection	
		if dic.has_key('VOUCHERTYPENAME') and dic['VOUCHERTYPENAME']: 
			VTYPE = dic['VOUCHERTYPENAME']
			
			if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']: 
				i = len(dic['ALLLEDGERENTRIES.LIST'])-1
			
			if VTYPE == 'Sales' or VTYPE == 'Debit Note':
				vtype = 'sale'
				VTYPE = 'Sale'
				ACC_ID = part_obj.property_account_receivable.id
				JR_ID = self.jrObj.search(cr, uid, [('name','=','Sale Journal'+' - ('+com.name+')')]) 
				
			elif VTYPE == 'Purchase' or VTYPE =='Credit Note':
				vtype = 'purchase'
				VTYPE = 'Purchase'
				ACC_ID = part_obj.property_account_payable.id
				JR_ID = self.jrObj.search(cr, uid, [('name','=','Purchase Journal'+' - ('+com.name+')')])
			
			elif VTYPE == 'Payment':
				vtype = 'payment'
				VTYPE = 'Payment'
				ACC_ID = part_obj.property_account_payable.id
				ledgerName = dic['ALLLEDGERENTRIES.LIST'][i]['LEDGERNAME']
				journalName = string.upper(ledgerName)+" - ("+com.name+")"
				JR_ID = self.jrObj.search(cr, uid, [('name','=',journalName)])
			
			elif VTYPE == 'Receipt' or VTYPE == 'Contra' or VTYPE == 'Journal':
				vtype = 'receipt'
				ACC_ID = part_obj.property_account_receivable.id
				ledgerName = dic['ALLLEDGERENTRIES.LIST'][i]['LEDGERNAME']
				journalName = string.upper(ledgerName)+" - ("+com.name+")"
				JR_ID = self.jrObj.search(cr, uid, [('name','=',journalName)])
		
		#deciding the entry :: is it misc. income/expence or indirect income/expence or not?? 
		if dic.has_key('ALLLEDGERENTRIES.LIST') and dic['ALLLEDGERENTRIES.LIST']:
			for i in dic['ALLLEDGERENTRIES.LIST']:
				#if 'ISPARTYLEDGER' == 'No', then entries goes to 'account.move'
				if i.has_key('ISPARTYLEDGER') and i['ISPARTYLEDGER']=='No':
					self.createAccountMove(cr, uid, dic, period_id[0], VTYPE, com)
					return True

		narration =''
		if dic.has_key('NARRATION') and dic['NARRATION']:
			NARRATION = dic['NARRATION']
		if dic.has_key('JOURNALID') and dic['JOURNALID']:
			JR_ID = [dic['JOURNALID']]

		data = {'type':vtype, 'date':DATE, 'journal_id':JR_ID[0], 'narration':NARRATION, 'company_id':com.id, 'state':'draft', 'account_id':ACC_ID, 'partner_id': part_obj.id, 'period_id':period_id[0]}
		
		vid = self.voucherObj.create(cr, uid, data)
		self.createAccountVoucherLine(cr, uid, dic, com, vid, VTYPE)
		
		return True

	def insertVoucherData(self, cr, uid, com, tallyData):

		a = tallyData['BODY']['IMPORTDATA']['REQUESTDATA']

		if a.has_key('TALLYMESSAGE'):
			l = len(a['TALLYMESSAGE'])
			dic = {}
			#If there is no records in tally.		
			if l<=0:
				pass

			#If there is only one record in tally.		
			elif l<2:  #for single record [TALLYMESSAGE] is dictionary.
				k = a['TALLYMESSAGE'].keys()[0]
				dic = a['TALLYMESSAGE'][k]
				if (k=='VOUCHER'):
					self.insertVouchers(cr, uid, dic ,com)

			#If there are multiple records in tally.	
			else:    #for multiple records [TALLYMESSAGE] is list of dictionaries.
				for i in a['TALLYMESSAGE']:
					k = i.keys()[0]
					dic = i[k]
					if (k=='VOUCHER'):
						self.insertVouchers(cr, uid, dic ,com)

		return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
