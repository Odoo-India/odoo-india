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

from psycopg2 import IntegrityError
from osv import osv
import string
import pooler
import migrator
import voucher
from datetime import datetime

code = 0
class ledgers():
	
	def insertRecords(self, cr, uid, dic, com, account, acc_type):
		global code
		parent = ""
		name = dic['NAME']
		
		if dic.has_key('PARENT') and dic['PARENT']:
			parent = dic['PARENT']
			domain = [('name','=',parent),('company_id','=',com.id)]	 
		else:
			#searching for the 'account' of the company.
			domain = [('name','=',com.name)]
		
		code += 1		
		parent_id = account.search(cr, uid, domain)

		#If 'parent_id' not found then create the account for that. 
		if not parent_id:

			# creating the 'account' for the company partner.
			data = {'name':com.name, 'code':string.upper(com.name[0:3]), 'type':'view', 'currency_mode':'current', 'user_type':1, 'company_id':com.id}
			try:
				parent_id = account.create(cr, uid, data)				
			except:
				raise osv.except_osv(('Error !'), ('Company code already exist please use another company name.'))

			
			# creating acc receivable and acc payable for specified company partner.
			migratorObj = migrator.migrator()
			poolObj = migratorObj.getPoolObj(cr)
			accTypObj = poolObj.get('account.account.type')
			
			#searching for Account Types
			payableType = accTypObj.search(cr, uid, [('name','=','Payable')])
			receivableType = accTypObj.search(cr, uid, [('name','=','Receivable')])

			#creating 'Account Payable' for the company partner.
			CrData = {'name':com.name+' (Creditors)', 'code':string.upper(com.name[0:3])+' (C)', 'type':'payable', 'currency_mode':'current', 'user_type':payableType[0], 'company_id':com.id, 'parent_id':parent_id}
			cr_id = account.create(cr, uid, CrData)

			#creating 'Account Receivable' for the company partner.
			DrData = {'name':com.name+' (Debtors)', 'code':string.upper(com.name[0:3])+' (D)', 'type':'receivable', 'currency_mode':'current', 'user_type':receivableType[0], 'company_id':com.id, 'parent_id':parent_id}
			dr_id = account.create(cr, uid, DrData)

			#assigning the 'property_account_receivable' and 'property_account_payable' for the 'company partner'
			partnerObj = poolObj.get('res.partner')
			partner_id = partnerObj.search(cr, uid, [('name','=',com.name),('company_id','=',com.id)])
			if partner_id:
				partnerData = {'customer':True, 'supplier':True, 'property_account_receivable':dr_id, 'property_account_payable':cr_id}
				partnerObj.write(cr, uid, partner_id, partnerData)
			else:
				raise osv.except_osv(('Error !'), ('Company Partner not found!! Please create a partner of the selected company first and then run the wizard again.'))

			#creating opening/closing situation journal.
			migratorObj = migrator.migrator()
			poolObj = migratorObj.getPoolObj(cr)
			journalObj = poolObj.get('account.journal')
			journalName = 'Opening/Closing'+" - ("+com.name+")"
			OpenJournalData = {'name':journalName, 'code':'OPN-'+com.name[0], 'type':'situation', 'default_debit_account_id':dr_id, 'default_credit_account_id':cr_id, 'company_id':com.id, 'view_id':3}
			open_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])

			if open_id:
				journalObj.write(cr, uid, open_id, OpenJournalData)
			else:
				open_id = journalObj.create(cr, uid, OpenJournalData)
				
		else:
		
			obj = account.browse(cr, uid, parent_id[0])
			p_code = obj.code
			typ = 0
			usr_typ = 0

			# if parent exist then 'user_type(Account Type)' and 'type(Internal Type)' for the child is same as parent.
			if parent:
				usr_typ = obj.user_type.id
				typ = obj.type
			#For the Parent Account we have to decide from dictionary key-value pair
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
					
			if name[:4] == 'Bank':
				typ = 'other'
			
			# creating double accounts(credit a/c and debit a/c) for res.partners and sales/purchase journals 
			contra_p_id	= []	
			if parent == 'Sundry Creditors':
				
				contra_u_typ = acc_type.search(cr, uid, [('code','=','asset')])
				domain = [('name','=','Sundry Debtors'),('company_id','=',com.id)]
				contra_parent_id = account.search(cr, uid, domain)
				contra_data = {'name':name+' (Debtors)', 'code':p_code + str(code), 'type':'receivable', 'parent_id':contra_parent_id[0], 'currency_mode':'current', 'user_type':contra_u_typ[0], 'company_id':com.id}
				code += 1
				
				try:
					domain = [('name','=',name+' (Debtors)'),('company_id','=',com.id)]
					contra_p_id = account.search(cr, uid, domain)
					if not contra_p_id:
						contra_p_id = account.create(cr, uid, contra_data)
						contra_p_id = [contra_p_id]
					else:
						code += 1
				
				except IntegrityError, e:
					code += 50
					raise osv.except_osv(('Unique Code Constraint Error'), ('Please Retry the Data Migration.'))
					
				#here we change the name, because related entry is created at below
				name = name + ' (Creditors)'
					
			elif parent == 'Sundry Debtors':
				
				contra_u_typ = acc_type.search(cr, uid, [('code','=','liability')])
				domain = [('name','=','Sundry Creditors'),('company_id','=',com.id)]
				contra_parent_id = account.search(cr, uid, domain)
				contra_data = {'name':name+' (Creditors)', 'code':p_code + str(code), 'type':'payable', 'parent_id':contra_parent_id[0], 'currency_mode':'current', 'user_type':contra_u_typ[0], 'company_id':com.id}
				code += 1
				
				try:
					domain = [('name','=',name+' (Creditors)'),('company_id','=',com.id)]
					contra_p_id = account.search(cr, uid, domain)
					if not contra_p_id:
						contra_p_id = account.create(cr, uid, contra_data)
						contra_p_id = [contra_p_id]
					else:
						code += 1
				
				except IntegrityError, e:
					code += 50
					raise osv.except_osv(('Unique Code Constraint Error'), ('Please Retry the Data Migration.'))
					
				#here we change the name, because related entry is created at below
				name = name + ' (Debtors)'
				 
			#creating the account of ledger
			data = {'name':name, 'code':p_code + str(code), 'type':typ, 'parent_id':parent_id[0], 'currency_mode':'current', 'user_type':usr_typ, 'company_id':com.id}
		
			try:
				
				domain = [('name','=',name),('company_id','=',com.id)]
				p_id = account.search(cr, uid, domain)
				
				# If 'p_id' is not found, then create a new account.
				if not p_id:
					p_id = account.create(cr, uid, data)
					p_id = [p_id]
				#else increase the 'code' by one
				else:
					code += 1
					
			except IntegrityError, e:
				code += 50
				raise osv.except_osv(('Unique Code Constraint Error'), ('Please Retry the Data Migration.'))
			
			#Creating Journals For Related Accounts
			try:
				#creating sales journal
				if name == 'Sales Accounts':  
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					journalObj = poolObj.get('account.journal')
					journalName = 'Sale Journal'+" - ("+com.name+")"
					SaleJournalData = {'name':journalName, 'code':'SAJ-'+com.name[0], 'type':'sale', 'default_debit_account_id':p_id[0], 'default_credit_account_id':p_id[0], 'company_id':com.id, 'view_id':4}
					saj_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])
		
					if saj_id:
						journalObj.write(cr, uid, saj_id, SaleJournalData)
					else:
						saj_id = journalObj.create(cr, uid, SaleJournalData)

				#creating purchase journal	
				elif name == 'Purchase Accounts': 
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					journalObj = poolObj.get('account.journal')
					journalName = 'Purchase Journal'+" - ("+com.name+")"
					PurchaseJournalData = {'name':journalName, 'code':'EXJ-'+com.name[0], 'type':'purchase', 'default_debit_account_id':p_id[0], 'default_credit_account_id':p_id[0], 'company_id':com.id, 'view_id':4}
					exj_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])
		
					if exj_id:
						journalObj.write(cr, uid, exj_id, PurchaseJournalData)
					else:
						exj_id = journalObj.create(cr, uid, PurchaseJournalData)
					
				# creating res.partner for sundry creditors/debtors	
				elif parent[:6] == 'Sundry': 
					name = dic['NAME']
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					partnerObj = poolObj.get('res.partner')
					PartnerData = {}
					if parent == 'Sundry Debtors':
						partnerData = {'property_account_payable':contra_p_id[0], 'property_account_receivable':p_id[0], 'customer':True, 'supplier':False, 'company_id':com.id}
					elif parent == 'Sundry Creditors':
						partnerData = {'property_account_payable':p_id[0], 'property_account_receivable':contra_p_id[0], 'supplier':True, 'customer':False, 'company_id':com.id}
					
					partner_id = partnerObj.search(cr, uid, [('name','=',name),('company_id','=',com.id)])
					if partner_id:
						partnerObj.write(cr, uid, partner_id, partnerData)
					else:
						partnerData['name'] = name
						partner_id = partnerObj.create(cr, uid, partnerData)
						
				# creating account.journal for bank
				elif parent[:4] == 'Bank': 
				
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					journalObj = poolObj.get('account.journal')
					journalName = string.upper(name)+" - ("+com.name+")"
					journalData = {'name':journalName, 'code':string.upper(name[0:5]), 'type':'bank', 'default_debit_account_id':p_id[0], 'default_credit_account_id':p_id[0], 'company_id':com.id, 'view_id':1}
					bank_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])
					
					if bank_id:
						journalObj.write(cr, uid, bank_id, journalData)
					else:
						bank_id = journalObj.create(cr, uid, journalData)

				# creating account.journal for cash		
				elif parent == 'Cash-in-hand': 
				
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					journalObj = poolObj.get('account.journal')
					journalName = string.upper(name)+" - ("+com.name+")"
					journalData = {'name':journalName, 'code':string.upper(name[0:5]), 'type':'cash', 'default_debit_account_id':p_id[0], 'default_credit_account_id':p_id[0], 'company_id':com.id, 'view_id':1}
					cash_id = journalObj.search(cr, uid, [('name','=',journalName),('company_id','=',com.id)])
					
					if cash_id:
						journalObj.write(cr, uid, cash_id, journalData)
					else:
						cash_id = journalObj.create(cr, uid, journalData)
						
				elif name == 'Reserves & Surplus':

					domain = [('name','=',com.name)]
					migratorObj = migrator.migrator()
					poolObj = migratorObj.getPoolObj(cr)
					compObj = poolObj.get('res.company')
					search_id = compObj.search(cr, uid, domain)
					if search_id:
						compObj.write(cr, uid, search_id, {'property_reserve_and_surplus_account':p_id[0]})
						
			except Exception, e:
				raise osv.except_osv(('Error!!!'), str(e))

			
			if dic.has_key('OPENINGBALANCE') and dic['OPENINGBALANCE']:
				opening_balance = float(dic['OPENINGBALANCE'])
				date = string.join(str(datetime.now())[:10].split("-"),"")

				migratorObj = migrator.migrator()
				poolObj = migratorObj.getPoolObj(cr)
				journalObj = poolObj.get('account.journal')

#				journalName = 'Opening/Closing'+" - ("+com.name+")"
#				domain = [('name','=',journalName),('company_id','=',com.id)]
				domain = [('type','=','situation'),('company_id','=',com.id)]
				search_id = journalObj.search(cr, uid, domain)

				#If 'OPENINGBALANCE' is positive then 'credit'
				#If 'OPENINGBALANCE' is negative then 'debit'
				voucherLineData = {'AMOUNT':opening_balance, 'LEDGERNAME':name, 'ISPARTYLEDGER':'Yes'}
				voucherData = {'DATE':date, 'PARTYLEDGERNAME':name, 'VOUCHERTYPENAME':'Receipt', 'NARRATION':'Opening Balance', 'ALLLEDGERENTRIES.LIST':[voucherLineData], 'JOURNALID':search_id[0]}

				voucherObj = voucher.voucher(cr)
				voucherObj.insertVouchers(cr, uid, voucherData ,com)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
				
					
					
					
