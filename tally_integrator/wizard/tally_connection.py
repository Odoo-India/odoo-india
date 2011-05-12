from osv import osv,fields
import os
import httplib
import etree_parser
import migrator
import connection

class tally_connection(osv.osv_memory):

	_name = 'tally.connection'
	_description = 'Tally Connection'
	

	_columns = {
		'url': fields.char('Tally URL With Port', size=256, required=True),
		'company': fields.many2one("res.company", "Migrate Data Into Company", required=True),
			
	}
	
	_defaults={'url':lambda * a:'http://localhost:9000',
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
			raise osv.except_osv(('Error !'), ('Error occured while connecting with Tally.'))
		
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
		
		#s = self.self.getData("Voucher types",conn)
		#s = self.getData("Units",conn)
		#s = self.getData("All Acctg. Masters",conn)
		#s = self.getData("All Inventory Masters",conn)
		#s = self.getData("All Statutory Masters",conn)
		s = self.getData("Ledgers",conn)
		#s = self.getData("Groups",conn)
		#s = self.getData("Cost Categories",conn)
		#s = self.getData("Cost Centers",conn)
		#s = self.getData("Godowns",conn)
		#s = self.getData("Stock Items",conn)
		#s = self.getData("Stock Groups",conn)
		#s = self.getData("Stock Categories",conn)  #{}
		#s = self.getData("Curriencies",conn)
		#s = self.getData("Employees",conn)
		#s = self.getData("Budgets & Scenarios",conn)  #{'LINEERROR': 'No XML Wrap!', '_text': 'Semi-colon ; expected.'}
		#s = self.getData("All Masters",conn)
		

		f = self.createTempFile(s)
		configdict = etree_parser.ConvertXmlToDict(f.name)
		tallyData = dict(configdict)
		migrator.insertData(cr, uid, company, tallyData)
		self.deleteTempFile() 
		return {}   

tally_connection()
