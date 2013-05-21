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
_logger = logging.getLogger("HR Employee")
import datetime

class import_hr_employee_data(osv.osv_memory):
    _name = "import.hr.employee.data"

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
    def import_hr_employee_data(self, cr, uid,ids, context=None):
        file_path = "/home/ashvin/Desktop/script/HRMAST.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Product Process from file '%s'."%(file_path))
        product_pool =self.pool.get('hr.employee')
        indent = []
        rejected =[]
        i = 0
        j = 0
        for data in data_lines:
            try:
                default_code = data["EMPNO"].strip()
                name=data["EMPNAME"].strip()
                emp_cost_code=data["EMPCOSTCOD"].strip()
                
                pf_no=data["PFNO"].strip()
                esicno=data["ESICNO"].strip()
                itaxno=data["ITAXNO"].strip()
                qua = data["QUALIFICATION"].strip()
                bld = data["BLOODGRP"].strip()
                
                street1 = data["ADD1"].strip()
                street2 = data["ADD2"].strip()
                street3 = data["ADD3"].strip()
                city = data["CITY"].strip()
                zip = data["PINCODE"].strip()
                phone = data["TELEPHON"].strip()
                mobile = data["MOBILE"].strip()
                
                vals = {
                        'emp_code':default_code,
                        'name':name,
                        'emp_cost_code':emp_cost_code,
                        }
                print "namenamename>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", type(name)
                address = self.pool.get('res.partner').search(cr,uid,[('name','=',name)])
                print "namenamename>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>addressaddressaddress>", address
                if not address:
                    address = self.pool.get('res.partner').create(cr,uid,{'name':name,
                                                                          'street':street1,
                                                                          'street2':street2,
                                                                          'street3':street3,
                                                                          'city':city,
                                                                          'zip':zip,
                                                                          'phone':phone,
                                                                          'mobile':mobile,
                                                                          })
                else:
                    address = address[0]
                vals_write = {
                      'pf_no':pf_no,
                      'esi_no':esicno,
                      'otherid':itaxno,
                      'qualification':qua,
                      'blood_group':bld,
                      'address_home_id':address
                      }
                hr_employee = self.pool.get('hr.employee').search(cr,uid,[('emp_code','=',default_code)])
                if not hr_employee:
                    p = product_pool.create(cr, uid, vals, context)
                    i = i+1
                else:
                    product_pool.write(cr, uid, hr_employee[0], vals_write, context)
                    j = j+1
            except:
                rejected.append(data['EMPNO'])
                _logger.warning("Skipping Record with EMPNO code '%s'."%(data['EMPNO']), exc_info=True)
                continue
        print "REJECTED Product", rejected
#        ppr = self.pool.get('product.product').search(cr,uid,[])
#        self.pool.get('product.product').write(cr,uid,ppr,{'state':'done'})
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_hr_employee_data()