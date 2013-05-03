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

class import_res_partner(osv.osv_memory):
    _name = "import.res.partner"
    
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
    
    def do_import_partner_data(self, cr, uid,ids, context=None):
        file_path = "/home/ron/Desktop/MAIZE/script/SUPLMST_all.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Supplier Process from file '%s'."%(file_path))
        indent = []
        rejected =[]
        for data in data_lines:
            try:
                SUPPCODE = data.get('SUPPCODE','')
                if SUPPCODE: SUPPCODE = SUPPCODE.strip()
                if not self.pool.get('res.partner').search(cr, uid, [('supp_code','=',SUPPCODE)]):
                    SUP_NAME = data.get('SUP_NAME','')
                    if SUP_NAME: SUP_NAME = SUP_NAME.strip()
                    SUP_DESCR = data.get('SUP_DESCR','')
                    if SUP_DESCR: SUP_DESCR = SUP_DESCR.strip()
                    ADDR1 = data.get('ADDR1','')
                    if ADDR1: ADDR1 = ADDR1.strip()
                    ADDR2 = data.get('ADDR2','')
                    if ADDR2: ADDR2 = ADDR2.strip()
                    ADDR3 = data.get('ADDR3','')
                    if ADDR3: ADDR3 = ADDR3.strip()
                    CITY =  data.get('CITY','')
                    if CITY: CITY = CITY.strip()
                    PIN =  data.get('PIN','')
                    if PIN: PIN = PIN.strip()
                    STATE = data.get('STATE','')
                    if STATE: STATE = STATE.strip()
                    if STATE:
                        if STATE == 'KARNATAK': STATE = 'KARNATAKA'
                        if STATE == 'DELHI                         ' or STATE == 'NEW DELHI': STATE = 'DELHI'
                        if STATE == 'UTTAR PRADESH                 ': STATE = 'UTTAR PRADESH'
                        if STATE == 'PONDICHERY': STATE = 'PONDICHERRY'
                        if STATE == 'CHHATISHGARDH': STATE = 'CHANDIGARH'
                        if STATE == 'MAHARASHTRA': STATE = 'MAHARASTRA'
                        if STATE == 'TAMIL NADU' or STATE =='TAMILNADU                     ': STATE = 'TAMILNADU'
                        if STATE == 'GUJRAT' or STATE == 'GUJAAT' or STATE == 'AHMEDABAD' or STATE == 'GUJARTAT': STATE = 'GUJARAT'
                        if STATE == 'PUNJAB                        ': STATE = 'PUNJAB'
                        if STATE == 'WEST BENGAL                   ': STATE = 'WEST BENGAL'
                        if STATE == 'UNITED STATE OF AMERICA' or STATE == 'U.S.A.': STATE = 'USA'
                        if STATE in('0265-2226004','CHINA','CIPUZKOA','TURKIYE','TURKEY','AUSTRIA','ELIZABETH WEST', 'GERMANY','  '): STATE = ''
                    state_id = False
                    if STATE:
                        state_id = self.pool.get('res.country.state').search(cr, uid, [('name','ilike',STATE)], context=context)
                    RAWCODE = data.get('RAWCODE',False)
                    if RAWCODE: RAWCODE = RAWCODE.strip()
                    row_code_id = False
                    if RAWCODE:
                        row_code_id = self.pool.get('row.code').search(cr, uid, [('code','ilike',RAWCODE)], context=context)
    
                    TAXCODE = data.get('TAXCODE',False)
                    if TAXCODE: TAXCODE = TAXCODE.strip()
                    tax_code_id = False
                    if TAXCODE:
                        tax_code_id = self.pool.get('tax.code').search(cr, uid, [('code','=',TAXCODE)], context=context)
    #                    
    #                if RAWCODE in ('M','m'): RAWCODE = 1
    #                elif RAWCODE in ('J','j'): RAWCODE = 2
    #                elif RAWCODE in ('C','c'): RAWCODE = 3
    #                elif RAWCODE in ('T','t'): RAWCODE = 4
    #                else: RAWCODE = False
                    
                    BANKCODE = data.get('BANKCODE',False)
                    if BANKCODE: BANKCODE = BANKCODE.strip()
                    bank_code_id = False
                    if BANKCODE:
                        bank_code_id = self.pool.get('account.journal').search(cr, uid, [('code','=',BANKCODE)], context=context)
                    
                    MDCODE = data.get('MDCODE','')
                    if MDCODE: MDCODE = MDCODE.strip()
                    PHONE =  data.get('PHONE','')
                    if PHONE: PHONE = PHONE.strip()
                    MOBILE = data.get('MOBILE','')
                    if MOBILE: MOBILE = MOBILE.strip()
                    SERIES =  data.get('SERIES','')
                    if SERIES: SERIES = SERIES.strip()
                    TDSPER =  data.get('TDSPER','')
                    if TDSPER: TDSPER = TDSPER.strip()
                    CFORMIND =  data.get('CFORMIND',False)
                    if CFORMIND: CFORMIND = CFORMIND.strip()
                    if CFORMIND == '1': CFORMIND = True
                    else: CFORMIND = False
                    FAX = data.get('FAX','')
                    if FAX: FAX = FAX.strip()
                    STNO_1 = data.get('STNO_1','')
                    if STNO_1: STNO_1 = STNO_1.strip()
                    STNO_2 = data.get('STNO_1','')
                    if STNO_2: STNO_2 = STNO_2.strip()
                    PANNO = data.get('PANNO','')
                    if PANNO: PANNO = PANNO.strip()
                    MAILID = data.get('MAILID','')
                    if MAILID: MAILID = MAILID.strip()
                    ECCCODE = data.get('ECCCODE','')
                    if ECCCODE: ECCCODE = ECCCODE.strip()
                    SERTAXREGNO = data.get('SERTAXREGNO','')
                    if SERTAXREGNO: SERTAXREGNO = SERTAXREGNO.strip()
                    CSTNO =  data.get('CSTNO','')
                    if CSTNO: CSTNO = CSTNO.strip()
                    vals = {
                            "supp_code":SUPPCODE,
                            "name":SUP_NAME,
                            "comment":SUP_DESCR,
                            "street":ADDR1,
                            "street2":ADDR2,
                            "street3":ADDR3,
                            "city":CITY,
                            "zip":PIN,
                            "state_id":state_id and state_id[0] or False,
                            "tax_code_id":tax_code_id and tax_code_id[0] or False,
                            "raw_code_id":row_code_id and row_code_id[0] or False,
                            "bank_code_id":bank_code_id and bank_code_id[0] or False,
                            "md_code":MDCODE,
                            "phone":PHONE,
                            "mobile":MOBILE,
                            "series_id":False,
                            "tds_per":TDSPER,
                            "c_form":CFORMIND,
                            "fax":FAX,
                            "pan_no":PANNO,#Temporarly not set because file have lot number which lenght not match to 10 character.
                            "email":MAILID,
                            "stno_1":STNO_1,
                            "stno_2":STNO_2,#Temporarly not set because file have lot number which lenght not match to 11 character.
                            "ecc_code":ECCCODE,
                            "ser_tax_reg_no":SERTAXREGNO,
                            "cst_no":CSTNO,
                            'supplier':True,
                            'is_company':True,
                            'company_id':1,
                            'co_code':'1',
    
                    }
                    ok = self.pool.get("res.partner").create(cr, uid, vals, context)
                else:
                    print "ALREADY EXIST",data['SUPPCODE']
            except:
                rejected.append(data['SUPPCODE'])
                _logger.warning("Skipping Record with Supplier code '%s'."%(data['SUPPCODE']), exc_info=True)
                continue
        print "rejectedrejectedrejected", rejected
        _logger.info("Successfully completed import Inward process.")
        return True
    
import_res_partner()