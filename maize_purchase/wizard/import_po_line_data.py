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

import time
import datetime
from openerp.osv import fields, osv
import csv
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_po_line_data(osv.osv_memory):
    _name = "import.po.line.data"
    def _get_start_end_date_from_year(self,cr,uid,year):
        po_year_start=''
        po_year_end=''
        if year =='20132014':
            po_year_start = '2013-04-01'
            po_year_end = '2014-03-31'
        elif year =='20122013':
            po_year_start = '2012-04-01'
            po_year_end = '2013-03-31'
        elif year =='20112012':
            po_year_start = '2011-04-01'
            po_year_end = '2012-03-31'
        elif year =='20102011':
            po_year_start = '2010-04-01'
            po_year_end = '2011-03-31'
        elif year =='20092010':
            po_year_start = '2009-04-01'
            po_year_end = '2010-03-31'
        elif year =='20082009':
            po_year_start = '2008-04-01'
            po_year_end = '2009-03-31'
        elif year =='20072008':
            po_year_start = '2007-04-01'
            po_year_end = '2008-03-31'
        elif year =='20062007':
            po_year_start = '2006-04-01'
            po_year_end = '2007-03-31'                                
        elif year =='20052006':
            po_year_start = '2005-04-01'
            po_year_end = '2006-03-31'
        elif year =='20042005':
            po_year_start = '2004-04-01'
            po_year_end = '2005-03-31'
        elif year =='20032004':
            po_year_start = '2003-04-01'
            po_year_end = '2004-03-31'
        elif year =='20022003':
            po_year_start = '2002-04-01'
            po_year_end = '2003-03-31'
        elif year =='20012002':
            po_year_start = '2001-04-01'
            po_year_end = '2002-03-31'
        elif year =='20002001':
            po_year_start = '2000-04-01'
            po_year_end = '2001-03-31'
        return {'start':po_year_start,'end':po_year_end}    
    def _read_csv_data(self, cr, uid, path, context=None):
        """
            Reads CSV from given path and Return list of dict with Mapping
        """
        data = csv.reader(open(path))
        # Read the column names from the first line of the file
        fields = data.next()
        data_lines = []
        for row in data:
            items = dict(zip(fields, row))
            data_lines.append(items)
        return fields,data_lines
    
    def po_line_create(self,cr,uid,ids,context=None):
        file_path = "/home/ara/Desktop/po_detail14july.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO LINE Process from file '%s'."%(file_path))
        pol_pool =self.pool.get('purchase.order.line')
        po_order = self.pool.get('purchase.order')
        indent = []
        rejected =[]
        exist_line=[]
        indent_not_found_list = []
        item_not_found = []
        project_not_match = []
        for data in data_lines:
            try:
                maize_name = data["POSERIES"] +'/'+ data["PONO"]+'/'+data['POYEAR']
                date_start = self._get_start_end_date_from_year(cr,uid,data['POYEAR'])['start']
                date_end = self._get_start_end_date_from_year(cr,uid,data['POYEAR'])['end']
                if maize_name:
                    po = self.pool.get('purchase.order').search(cr,uid,[('maize','=',maize_name)])
                if data["ITEMCODE"]:
                    try:
                        product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                        prod_name1 = self.pool.get('product.product').read(cr, uid, product,['name'])['name']
                        prod_name2 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
                        prod_name3 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
                        prod_name4 = self.pool.get('product.product').read(cr, uid, product,['desc3'])['desc3']
                    except:
                        item_not_found.append(data["ITEMCODE"])
                if data["PORATE"]:
                    rate = data["PORATE"]
                department=False
                if data["DEPTCODE"].strip():
                    if len(data["DEPTCODE"].strip()) == 1:
                        dept = '00'+data["DEPTCODE"].strip()
                    elif len(data["DEPTCODE"].strip()) == 2:
                        dept = '0'+data["DEPTCODE"].strip()
                    elif len(data["DEPTCODE"].strip()) == 3:
                        dept = data["DEPTCODE"].strip()
                    department = self.pool.get('stock.location').search(cr, uid,[('code','=',dept)])[0]
                    
                mach = False
                if len(data["MACHCODE"].strip()) == 1:
                    mach = '00'+data["MACHCODE"].strip()
                elif len(data["MACHCODE"].strip()) == 2:
                    mach = '0'+data["MACHCODE"].strip()
                elif len(data["MACHCODE"].strip()) == 3:
                    mach = data["MACHCODE"].strip()                
                project=False
                if mach:
                    try:
                        project = self.pool.get('account.analytic.account').search(cr,uid,[('code','=',mach)])[0]
                    except:
                        project_not_match.append(mach)
                if data["DISCPER"]:
                    discount = data["DISCPER"]
                    #self.pool.get('purchase.order').write(cr,uid,po[0],{'discount_percentage':discount})

                indent_id=False
                indentor_id=False
                fiscalyear = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',data['INDYEAR'].strip())])
                if data["INDENTNO"] and fiscalyear:
                    indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"]), ('fiscalyear','=',fiscalyear[0])])
                    indent_id = indent and indent[0] or False
                if data["INDENTOR"]:
                    indentor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])
                    indentor_id = indentor and indentor[0] or ''
                if data["SQTY"]:
                    qty = data["SQTY"]
                    
                if data["DLVDATE"]:
                    if data["DLVDATE"] == 'NULL' or data["DLVDATE"] == '' or data["DLVDATE"] == '00:00.0' or data["DLVDATE"] == '  ':
                        dlv_date = ''
                    else:
                        dlv_date=datetime.datetime.strptime(data["DLVDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                vals = {'order_id':po[0],
                        'product_id':product,
                        'price_unit':rate,
                        #'discount': discount,
                        'name':prod_name1 or ''+'\n'+prod_name2 or ''+'\n'+prod_name3 or ''+'\n'+prod_name4 or '',
                        'product_qty':qty,
                        'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                        'date_planned':dlv_date,
                        #'freight':freight_rs,
                        'indent_id':indent_id and int(indent_id) or '',
                        'indentor_id':indentor_id and int(indentor_id) or '',
                        'department_id':department or '',
                        'account_analytic_id':project or '',
                        'discount':discount
                       }
                exist_line.append(maize_name)
                if int(data['INDENTNO']) == 0:
                    exist_po_line = pol_pool.search(cr,uid,[('order_id','=',po[0]), ('product_id', '=', product)])
                else:
                    exist_po_line = pol_pool.search(cr,uid,[('order_id','=',po[0]),('indent_id', '=', data['INDENTNO']), ('product_id', '=', product)])  
                if not exist_po_line:
                    po_line = pol_pool.create(cr, uid, vals, context)
                    print "=----po_line-newwwwww-->>", po_line
                #po_order.write(cr,uid,po[0],{'commission':0.01})
                #po_order.write(cr,uid,po[0],{'commission':0.00})
                else:
                    print "=----exist_po_line--->>", exist_po_line,maize_name
            except:
                rejected.append(maize_name)
                _logger.warning("Skipping Record with Indent code '%s'."%(maize_name), exc_info=True)
                continue
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", rejected,
        print "project_not_matchproject_not_matchproject_not_match", project_not_match
        print ">>>>item_not_founditem_not_founditem_not_found", item_not_found
        #aaa = self.pool.get('purchase.order').search(cr,uid,[])
#         self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.01})
#         self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.00})
        return True
import_po_line_data()
