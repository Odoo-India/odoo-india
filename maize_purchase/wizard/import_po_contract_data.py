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

class import_po_contract_data(osv.osv_memory):
    _name = "import.po.contract.data"
    
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
    
    def do_import_po_contract_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/ara/Desktop/odt/indent/contract.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import CONTRACT HEADER Process from file '%s'."%(file_path))
        po_pool =self.pool.get('purchase.order')
        seq_obj = self.pool.get('ir.sequence')
        indent = []
        rejected =[]
        exist = []
        total_po_for_update = []
        project_not_match = []
        un_define= []
        product_not_found = []
        for data in data_lines:
            try:
                name = data["JOBNO"]
                search_for_contract = data["JOBNO1"]+'/'+data["JOBYEAR"]
                search_for_indent = data["JOBNO1"].strip()
                if not search_for_contract in exist:
                    exist.append(search_for_contract)
    
                    if data["JOBSERIES"]:
                        po_series = self.pool.get('product.order.series').search(cr,uid,[('code','=',data["JOBSERIES"].strip()),('type','=','indent')])[0]
                       #co_series = self.pool.get('product.order.series').search(cr,uid,[('code','=','CO')])[0]
                        
                    if data["JOBDATE"]:
                        if data["JOBDATE"] == 'NULL' or data["JOBDATE"] == '' or data["JOBDATE"] == '00:00.0' or data["JOBDATE"] == '  ':
                            value = ''
                        else:
                            value=datetime.datetime.strptime(data["JOBDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                        podate = value
    
                    if data["FROMDATE"]:
                        if data["FROMDATE"] == 'NULL' or data["FROMDATE"] == '' or data["FROMDATE"] == '00:00.0' or data["FROMDATE"] == '  ':
                            value = ''
                        else:
                            value=datetime.datetime.strptime(data["FROMDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                        fdate = value
                        
                    if data["TODATE"]:
                        if data["TODATE"] == 'NULL' or data["TODATE"] == '' or data["TODATE"] == '00:00.0' or data["TODATE"] == '  ':
                            value = ''
                        else:
                            value=datetime.datetime.strptime(data["TODATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                        tdate = value
                        
                    if data["SUPPCODE"]:
                        partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','ilike',data["SUPPCODE"])])
                        try:
                            partner = partner[0]
                        except:
                            un_define.append(data["SUPPCODE"])
                    delivey = ''
                        
                    if data["DAYS"]:
                        total_days = data["DAYS"]
                        
                    if data["RETIND"] == 'Y':
                        ret = 'leived'
                    else:
                        ret = 'not_leived'
    
                    ins = 0.0
                    ins_type = 'fix'
                    note = ''
                    if data["REMARK"]:
                        note= data["REMARK"]
                        
                    if data["STKRATE"]:
                        rate = data["STKRATE"]
                        
                    if data["ISUQTY"]:
                        qty = data["ISUQTY"]

                    #To find Department
                    department=False
                    departner_name = data["DEPTCODE"].strip()
                    if departner_name:
                        if len(departner_name) == 1:
                            dept = '00'+departner_name
                        elif len(departner_name) == 2:
                            dept = '0'+departner_name
                        elif len(departner_name) == 3:
                            dept = departner_name
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

                    #To find Indentor
                    indentor_id = False
                    if data.get('INDENTOR'):
                        indentor_ids = self.pool.get('res.users').search(cr,uid,[('user_code','=',data['INDENTOR'])])
                        if indentor_ids: indentor_id = indentor_ids[0]

                    #To find indent
                    indent_name = ''
                    indent_obj = self.pool.get('indent.indent')
                    print "????", search_for_indent
                    indent = indent_obj.search(cr, uid, [('maize','=',search_for_indent)])
                    if indent:
                        indent_name = indent_obj.browse(cr, uid, indent[0]).name

                    if data["ITEMCODE"]:
                        try:
                            product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                        except:
                            product_not_found.append(data["ITEMCODE"])
                    vals_line = {
                            'product_id':product,
                            'price_unit':float(rate),
                            'name':'test',
                            'product_qty':qty,
                            'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date_planned':'03/29/2013',
                            'indentor_id':indentor_id,
                            'indent_id':indent[0],
                            'department_id':department or False,
                            'account_analytic_id':project or False,
                           }
                    vals = {
                            'name':data["JOBSERIES"]+'/'+data["JOBNO"]+'/'+data["JOBYEAR"],
                            'maize':data["JOBSERIES"]+'/'+data["JOBNO"]+'/'+data["JOBYEAR"],
                            'origin':indent_name,
                            #'po_series_id':co_series,
                            'contract_id':po_series,
                            'date_order':podate,
                            'date_from':fdate,
                            'date_to':tdate,
                            'partner_id': partner,
                            'delivey':delivey,
                            'location_id':12,
                            'pricelist_id':2,
                            'insurance':ins,
                            'insurance_type':ins_type,
                            'no_of_days1':total_days,
                            'total_days':total_days,
                            'retention':ret,
                            'order_line':[(0,0,vals_line)],
                            'notes':note,
                           }
                    data['po'] = po_pool.create(cr, uid, vals, context)

                    #This lines for only update Po's total amount.
                    #po_pool.write(cr,uid,data['po'],{'other_discount':0.1})
                    #po_pool.write(cr,uid,data['po'],{'other_discount':0.0})
                    #Update directly contract field
                    #cr.execute(""" update purchase_order set contract=True WHERE id = %s""" , (data['po'],))
                else:
                    print "search_for_contractsearch_for_contract>>>", search_for_contract
                    po = self.pool.get('purchase.order').search(cr,uid,[('maize','=',search_for_contract), ('contract','=',True)])
                    if data["ISUQTY"]:
                        qty = data["ISUQTY"]
                    if data["STKRATE"]:
                        rate = data["STKRATE"]

                    if data["ITEMCODE"]:
                        try:
                            product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                        except:
                            product_not_found.append(data["ITEMCODE"])

                    #To find Indentor
                    indentor_id = False
                    if data.get('INDENTOR'):
                        indentor_ids = self.pool.get('res.users').search(cr,uid,[('user_code','=',data['INDENTOR'])])
                        if indentor_ids: indentor_id = indentor_ids[0]

                    #To find Department
                    department=False
                    departner_name = data["DEPTCODE"].strip()
                    if departner_name:
                        if len(departner_name) == 1:
                            dept = '00'+departner_name
                        elif len(departner_name) == 2:
                            dept = '0'+departner_name
                        elif len(departner_name) == 3:
                            dept = departner_name
                    department = self.pool.get('stock.location').search(cr, uid,[('code','=',dept)])[0]

                    #To find Project
                    mach=False
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

                    vals_line = {
                            'product_id':product,
                            'price_unit':float(rate),
                            'name':'test',
                            'product_qty':qty,
                            'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date_planned':'03/29/2013',
                            'indentor_id':indentor_id,
                            'department_id':department or False,
                            'account_analytic_id':project or False,
                           }
                    po_pool.write(cr, uid,po[0], {'order_line':[(0,0,vals_line)]}, context)
                    #This lines for only update Po's total amount.
                    po_pool.write(cr,uid,po[0],{'other_discount':0.1})
                    po_pool.write(cr,uid,po[0],{'other_discount':0.0})
                    #Update directly contract field
                    #cr.execute(""" update purchase_order set contract=True WHERE id = %s""" , (po[0],))

            except:
                rejected.append(data['JOBNO'])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['JOBNO']), exc_info=True)
                continue
#        aaa = self.pool.get('purchase.order').search(cr,uid,[])
#        self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.01})
#        self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.00})
        print "rejectedrejectedrejected>>>>>>>>>>>>>", rejected
        print "project_not_matchproject_not_match>>>",project_not_match
        print "partner not found", un_define
        print "partner not found", un_define
        _logger.info("Successfully completed import journal process.")
        return True
    
import_po_contract_data()