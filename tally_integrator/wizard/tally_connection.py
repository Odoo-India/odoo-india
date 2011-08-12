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

from osv import osv,fields
import os
import etree_parser
import migrator
import connection
import voucher

class tally_connection(osv.osv_memory):

	_name = 'tally.connection'
	_description = 'Tally Connection'
	
	def onchange_vouchers_option(self, cr, uid, ids, vouchers):
		if vouchers == True:
			return {'value':{'ledgers': True, 'groups': True}}
		else:
			return {'value':{'ledgers': False, 'groups': False}}
	
	def onchange_ledgers_option(self, cr, uid, ids, ledgers):
		if ledgers == True:
			return {'value':{'groups': True}}
		else:
			return {'value':{'groups': False}}

	def onchange_inventory_master_option(self, cr, uid, ids, inventory_master):
		if inventory_master == True:
			return {'value':{'stock_items': True, 'stock_groups': True, 'units': True, 'godowns': True}}
		else:
			return {'value':{'stock_items': False, 'stock_groups': False, 'units': False ,'godowns': False}}

	def onchange_stock_items_option(self, cr, uid, ids, stock_items):
		if stock_items == True:
			return {'value':{'stock_groups': True, 'units': True, 'godowns': True}}
		else:
			return {'value':{'stock_groups': False, 'units': False ,'godowns': False}}

	_columns = {
		'url': fields.char('Tally URL With Port', size=256, required=True),
		'company': fields.many2one("res.company", "Migrate Data Into Company"),
		'daybook': fields.char('Path To DayBook', size=256,  help='Export the DayBook in XML Format, and give the path of DayBook.xml file.'),
		'ledgers': fields.boolean('Ledgers'),
		'groups': fields.boolean('Groups'),
		'vouchers': fields.boolean('Vouchers'),
		'inventory_master': fields.boolean('All Inventory Masters'),
		'stock_items': fields.boolean('Stock Items'),
		'stock_groups': fields.boolean('Stock Groups'),
		'units': fields.boolean('Unit of Measure'),
		'employees' : fields.boolean('Employees'),
		'godowns' : fields.boolean('Godowns'),
	}
	
	_defaults={
		'url':lambda * a:'http://localhost:9000',
		'daybook': '/home/mdi/.wine/dosdevices/c:/Tally/DayBook.xml'
	}
	
	def getData(self,reportType,conn):
		headers = {"Content-type": "text/xml", "Accept": "text/xml"}
		params = """<ENVELOPE>
		  <HEADER>
		  <TALLYREQUEST>Export Data</TALLYREQUEST> 
		  </HEADER>
		  <BODY>
		  <EXPORTDATA>
		  <REQUESTDESC>
		  <REPORTNAME>List of Accounts</REPORTNAME> 
		  <STATICVARIABLES>
		  <SVEXPORTFORMAT>Windows:XML</SVEXPORTFORMAT> 
		  <ACCOUNTTYPE>""" + reportType + """</ACCOUNTTYPE> 
		  </STATICVARIABLES>
		  </REQUESTDESC>
		  </EXPORTDATA>
		  </BODY>
		</ENVELOPE>"""
		
		try:
			conn.request("POST", "/", params, headers)
		except:
			raise osv.except_osv(('Error !'), ('Error Occured While Connecting With Tally.'))
		
		r1 = conn.getresponse()
		return r1.read()

	def createTempFile(self,s):
		f = open('temp.xml','w')
		f.write(s)
		f.close()
		return f

	def deleteTempFile(self):
		os.remove(os.path.abspath('temp.xml'))
		return True

	def tally_main(self, cr, uid, ids, context=None):
		
		form_obj = self.pool.get('tally.connection')
		obj = form_obj.browse(cr, uid, ids[0], context=context)
		conn = connection.make_connection(obj.url)
		company = obj.company
		daybook = obj.daybook
		
		def _processData(s):
			f = self.createTempFile(s)
			configdict = etree_parser.ConvertXmlToDict(f.name)
			if not configdict:
				return {}
			tallyData = dict(configdict)
			obj_migrator = migrator.migrator()
			obj_migrator.insertData(cr, uid, company, tallyData)
			self.deleteTempFile()
		
		if obj.ledgers:
			s = self.getData("Ledgers",conn)
			_processData(s)
		elif obj.groups:
			s = self.getData("Groups",conn)
			_processData(s)
			
		if obj.vouchers:
			s = self.getData("Ledgers",conn)
			_processData(s)
			try:
				configdict = etree_parser.ConvertXmlToDict(daybook)
			except Exception, e:
				raise osv.except_osv(('No such file or directory'), str(e))
			if not configdict:
				return {}
			tallyData = dict(configdict)
			obj_voucher = voucher.voucher(cr)
			obj_voucher.insertVoucherData(cr, uid, company, tallyData)

		if obj.inventory_master:
			s = self.getData("All Inventory Masters",conn)
			_processData(s)	
		elif obj.stock_items:
			s = self.getData("Stock Items",conn)
			_processData(s)	
		elif obj.stock_groups:
			s = self.getData("Stock Groups",conn)
			_processData(s)

		if obj.units and not obj.stock_items and not obj.inventory_master:
			s = self.getData("Units",conn)
			_processData(s)
		
		if obj.godowns:
			s = self.getData("Godowns",conn)
			_processData(s)	
			
		if obj.employees:
			s = self.getData("Employees",conn)
			_processData(s)
					
		return {}   

tally_connection()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
