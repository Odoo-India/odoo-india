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
_logger = logging.getLogger("Product product")
import datetime

class import_product_data(osv.osv_memory):
    _name = "import.product.data"

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

    #TODO:FIX ME TO FIND INDENT
    def import_product_data(self, cr, uid,ids, context=None):
        file_path = "/home/ara/Desktop/script/product.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Product Process from file '%s'."%(file_path))
        product_pool =self.pool.get('product.product')
        indent = []
        rejected =[]
        i = 0
        for data in data_lines:
            try:
                default_code = data["ITEMCODE"].strip()
                name=data["DESCR1"].strip()
                desc2=data["DESCR2"].strip()
                desc3=data["DESCR3"].strip()
                desc4=data["DESCR4"].strip()
                uom_id=data["UNIT"].strip()
                uom_po_id=data["UNIT"].strip()
                variance=data["VARIANCE"].strip()
                item_type=data["ITEMTYPE"].strip()
                #"purchase_requisition":"1",
                location=data["LOCATION"].strip()
                ex_chapter=data["EXCHAPTER"].strip()
                ex_chapter_desc=data["EXCHAPTERDESCR"].strip()
                last_po_date=data["LPODATE"].strip()
                last_po_year=data["LPOYEAR"].strip()
                #"last_po_no":"LPONUMBER",
                last_supplier_code=data["LSUPPCODE"].strip()
                last_supplier_rate=data["LSUPPRATE"].strip()
                last_po_series=data["LPOSERIES"].strip()
                last_issue_date = data["LISSUDATE"].strip()
                if default_code:
                    default_code = '0'+default_code
                prod = self.pool.get('product.product').search(cr,uid,[('default_code','=',default_code)])
                if not prod:                    
                    if last_po_series:
                        if last_po_series == ' ':
                            last_po_series = ''
                        else:
                            l_po_series = self.pool.get('product.order.series').search(cr,uid,[('code','=',last_po_series)])
                            if l_po_series:
                                last_po_series = l_po_series[0]
                            else:
                                last_po_series = False
                    if uom_id:
                        uom = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_id)])
                        if uom:
                            uom_id = uom_po_id = uom[0]
                            
                        else:
                            uom_id = uom_po_id = ''
                    if item_type:
                        if item_type == '  ':
                            item_type = ''
                        item_type = item_type.lower()
                    if last_po_date:
                        if last_po_date == 'NULL' or last_po_date == '' or last_po_date == '00:00.0' or last_po_date == '  ' or last_po_date == ' ':
                            last_po_date = False
                        else:
                            last_po_date=datetime.datetime.strptime(last_po_date, '%d-%m-%Y').strftime("%Y-%m-%d")
    
                    if last_issue_date:
                        if last_issue_date == 'NULL' or last_issue_date == '' or last_issue_date == '00:00.0' or last_issue_date == '  ' or last_issue_date == ' ':
                            last_issue_date = False
                        else:
                            last_issue_date=datetime.datetime.strptime(last_issue_date, '%d-%m-%Y').strftime("%Y-%m-%d")
    
    
                    if last_supplier_code:
                        last_supplier_code = last_supplier_code[1:]
                        supplier = self.pool.get("res.partner").search(cr,uid,[('supp_code','=',last_supplier_code)])
                        if supplier == [] or supplier == False:
                            un_sup = self.pool.get("res.partner").search(cr,uid,[('supp_code','=','1111111'),('name','=','Undefine Supplier')])
                            if not un_sup:
                                un_sup = [self.pool.get("res.partner").create({'name':'Undefine Supplier','supp_code':'1111111','supplier':True,'active':True})]
                            last_supplier_code=un_sup[0]
                        else:
                            last_supplier_code=supplier[0]
    
                    if default_code:
                        #fields.append('type')
                        if default_code[0:4]=='0192':
                            type = 'service'
                            purchase_requisition = False
                        else:
                            type = 'product'
                            purchase_requisition = True
    
                    if default_code:
                        #fields.append('categ_id')
                        if default_code[0:2] == "01":
                            categ_id = 1
                        elif default_code[0:2] == "02":
                            categ_id = 2
                            
                        #fields.append('major_group_id/.id')
                        major = self.pool.get("product.major.group").search(cr,uid,[('code','=',default_code[2:4])])
                        major_group_id = major[0]
                        
                        sub = self.pool.get("product.sub.group").search(cr,uid,[('major_group_id','=',default_code[2:4]),('code','=',default_code[4:6])])
                        #fields.append('sub_group_id/.id')
                        sub_group_id = sub[0]
                    if last_supplier_rate == 'NULL':
                        last_supplier_rate=''
    
                    vals = {
                            'default_code':default_code,
                            'name':name,
                            'desc2':desc2,
                            'desc3':desc3,
                            'desc4':desc4,
                            'uom_id':uom_id,
                            'uom_po_id':uom_po_id,
                            'variance':variance,
                            'item_type':item_type,
                            #"purchase_requisition":"1",
                            'location':location,
                            'ex_chapter':ex_chapter,
                            'ex_chapter_desc':ex_chapter_desc,
                            'last_po_date':last_po_date,
                            'last_po_year':last_po_year,
                            #"last_po_no":"LPONUMBER",
                            'last_supplier_code':last_supplier_code,
                            'last_supplier_rate':last_supplier_rate,
                            'list_price':last_supplier_rate,
                            'last_po_series':last_po_series,
                            'type':type,
                            'purchase_requisition':purchase_requisition,
                            'categ_id':categ_id,
                            'major_group_id':major_group_id,
                            'sub_group_id':sub_group_id,
                            'state':'done',
                            'last_issue_date':last_issue_date
                            }
                    prod = self.pool.get('product.product').search(cr,uid,[('default_code','=',default_code)])
                    if not prod:
                        product_pool.create(cr, uid, vals, context)
                        i = i+1
                        print ">>>>>>>>>>>>>>",i
                else:
                    product_pool.write(cr, uid, prod[0],{'list_price':last_supplier_rate}, context)
                    i = i+1
                    print ">>>>>>>>>>>>>>222222222",i
            except:
                rejected.append(data['ITEMCODE'])
                _logger.warning("Skipping Record with Itemcode code '%s'."%(data['ITEMCODE']), exc_info=True)
                continue
        print "REJECTED Product", rejected
#        ppr = self.pool.get('product.product').search(cr,uid,[])
#        self.pool.get('product.product').write(cr,uid,ppr,{'state':'done'})
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_product_data()