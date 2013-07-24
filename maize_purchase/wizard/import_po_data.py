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

class import_po_data(osv.osv_memory):
    _name = "import.po.data"
    
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
    def do_import_po_data(self, cr, uid,ids, context=None):
#         all_po = po_pool.search(cr,uid,[])
#         po_pool.write(cr,uid,all_po,{'commission':0.01})
#         po_pool.write(cr,uid,all_po,{'commission':0.00})
        po_pool = self.pool.get('purchase.order') 
        file_path = "/home/ara/Desktop/ponot20132014butinward20132014.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            
  
        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
          
        indent = []
        rejected =[]
        partner = []
        un_define = []
        note=''
        for data in data_lines:
            try:
#                if data['APRVID'] == 'Y':
#                    wf_service = netsvc.LocalService('workflow')
#                    indent = self.pool.get('indent.indent').search(cr,uid,[('name','=',data["INDENTNO"])])[0]
#                    wf_service.trg_validate(uid, 'indent.indent', indent, 'indent_inprogress', cr)
#                print "data111111111111111111111111", data["INDENTOR"]
  
                if data["PONO"]:
                    name = data["POSERIES"]+'/'+ data["PONO"]+'/'+data["POYEAR"]
#                 if data["PONO"] and data["POSERIES"]:
#                     old_id = name
  
                if data["POSERIES"]:
                    print ">>>>>>>>>>>", data["POSERIES"]
                    po_series = self.pool.get('product.order.series').search(cr,uid,[('code','=',str(data["POSERIES"]))])[0]
                      
                if data["PODATE"]:
                    if data["PODATE"] == 'NULL' or data["PODATE"] == '' or data["PODATE"] == '00:00.0' or data["PODATE"] == '  ':
                        value = ''
                    else:
                        value=datetime.datetime.strptime(data["PODATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                    podate = value
                      
                if data["SUPPCODE"]:
                    partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',data["SUPPCODE"])])
                    #un_define = self.pool.get('res.partner').search(cr,uid,[('supp_code','=','1111111')])
                    try:
                        if partner:
                            partner = partner[0]
                    except:
                        un_define.append(data["SUPPCODE"])
                        
                if data["MILDELIV"]:
                    delv = self.pool.get('purchase.delivery')
                    delivery = delv.search(cr,uid,[('name','=',data["MILDELIV"])])
                    if delivery:
                        delivey = delivery[0]
                    else:
                        delivey = delv.create(cr,uid,{'name':data["MILDELIV"],'code':data["MILDELIV"]})
  
                if data["INSURANCE"]:
                    ins = 0.0
                if data["INSAMOUNT"]:
                    ins_type = 'fix'
                yourref = ''
                ourref = ''
                if data["YOURREF"]:
                    yourref = data["YOURREF"]
                if data["OURREF"]:
                    ourref = data["OURREF"]                    
                      
                if data["EXCISE"]:
                    data["EXCISE"] = int(data["EXCISE"])
                    if data["EXCISE"] == 0:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','=','No Excise')])
                    elif data["EXCISE"] == 1:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','=',' Excise Duty paid')])
                    elif data["EXCISE"] == 2:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','=',' Excise @ 12.36% (Edu Cess 2% + H. Edu Cess 1%)')])
                    elif data["EXCISE"] == 3:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','=',data["EXCISEPER"]+' per unit (Edu.cess 2% + H.Edu cess 1%)')])
                    if not excies:
                        excies = [self.pool.get("account.tax").create(cr,uid,
                                                                      {'name':data["EXCISEPER"]+' per unit (Edu.cess 2% + H.Edu cess 1%)',
                                                                       'tax_type':'excise',
                                                                       'sequence':1,
                                                                       'type':'fixed',
                                                                       'include_base_amount':True,
                                                                       'amount':data["EXCISEPER"]})]
                        self.pool.get("account.tax").create(cr,uid,
                                                                      {'name':'Edu.cess 2% on '+data["EXCISEPER"],
                                                                       'tax_type':'excise',
                                                                       'sequence':10,
                                                                       'type':'percent',
                                                                       'amount':0.02,
                                                                       'include_base_amount':False,
                                                                       'parent_id':excies[0]})
                        self.pool.get("account.tax").create(cr,uid,
                                                                      {'name':'Edu.cess 1% on '+data["EXCISEPER"],
                                                                       'tax_type':'excise',
                                                                       'sequence':15,
                                                                       'type':'percent',
                                                                       'amount':0.01,
                                                                       'include_base_amount':False,
                                                                       'parent_id':excies[0]})
                              
#                            child_2per = self.pool.get("account.tax").create(cr,uid,{'name':'Edu Cess 2%',
#                                                                                     'tax_type':'excise',
#                                                                                     'sequence':10,
#                                                                                     'type':'percent',
#                                                                                     'amount':0.02,
#                                                                                     'parent_id':excies[0]})
                    excies_ids = [(6,0,excies)]
                vat = []
                if data["SALETAX"]:
                    data["SALETAX"] = int(data["SALETAX"])
                    if data["SALETAX"] == 0:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','=','VAT Paid')])
                    elif data["SALETAX"] == 1:
                        if data["SALETAXPER1"] == '4':#for sales tax 5
                            vat = self.pool.get("account.tax").search(cr,uid,['|',('name','=','VAT @ 4%'), ('name','=','Add VAT @ 1%')])
                        elif data["SALETAXPER1"] == '12.5':#for sales tax 15
                            vat = self.pool.get("account.tax").search(cr,uid,['|',('name','=','VAT @ 12.5%'), ('name','=','VAT @ 2.5%')])
                        elif data["SALETAXPER1"] == '15':#for sales tax 17.5
                            vat = self.pool.get("account.tax").search(cr,uid,['|',('name','=','VAT @ 15%'),('name','=','VAT @ 2.5%')])
                    elif data["SALETAX"] == 2:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','=',"C.S.T")])
                    elif data["SALETAX"] == 3:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','=',"2.00 % C Form to be Issued")])
                    elif data["SALETAX"] == 4:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','=',"Tax Extra")])
                    elif data["SALETAX"] == 5:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','=',"'H' form to be Issued")])
                    elif data["SALETAX"] == 6:
                        if data["SALETAXPER1"] == '12.36':
                            vat = self.pool.get("account.tax").search(cr,uid,[('name','=','VAT @ 12.36%')])
                    vat_ids = [(6,0,vat)]
                      
                if data["REMARK1"] or data["REMARK2"] or data["REMARK3"] or data["REMARK4"]:
                    note= data["REMARK1"] +'\n'+ data["REMARK2"] +'\n'+ data["REMARK3"] +'\n'+ data["REMARK4"]
                      
                freight_rs = 0.0
                if data["FREIGHTRS"] and data["EXITEMS"]:
                    aa = float(data["EXITEMS"])
                    if aa > 0:
                        freight_rs = float(data["FREIGHTRS"])/aa
                      
                if data["PAYTERM"]:
                    pay_obj = self.pool.get('account.payment.term')
                    payment_term = pay_obj.search(cr,uid,[('name','=',data["PAYTERM"])])
                    if payment_term:
                        payment_term = payment_term[0]
                    else:
                        payment_term = pay_obj.create(cr,uid,{'name':data["PAYTERM"],'note':data["PAYTERM"],'active':True})
                vals = {'name':name,
                        'maize':name,
                        'po_series_id':po_series,
                        'date_order':podate,
                        'partner_id': partner,
                        'delivey':delivey,
                        'location_id':299,
                        'pricelist_id':2,
                        'insurance':ins,
                        'insurance_type':ins_type,
                        'excies_ids':excies_ids,
                        'vat_ids':vat_ids,
                        'notes':note,
                        'payment_term_id':payment_term,
                        'freight':freight_rs,
                        'your_ref':yourref,
                        'our_ref':ourref,
                                                   }
                #date_start = self._get_start_end_date_from_year(cr,uid,data['POYEAR'])['start']
                # date_end = self._get_start_end_date_from_year(cr,uid,data['POYEAR'])['end']
                exist_po = po_pool.search(cr,uid,[('maize','=',name)])
                if not exist_po:
                    po_pool.create(cr, uid, vals, context)
                  
            except:
                rejected.append(data["POSERIES"] + '/' +data["PONO"])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['SUPPCODE']), exc_info=True)
                continue
        print "rejectedrejectedrejected>> supplier not found", rejected,un_define
        _logger.info("Successfully completed import PO process.")
        return True
   
import_po_data()