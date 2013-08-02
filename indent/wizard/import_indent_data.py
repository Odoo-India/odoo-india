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
import os
from datetime import datetime
from openerp.osv import fields, osv
import csv
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_indent_data(osv.osv_memory):
    _name = "import.indent.data"
    
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

    def _write_bounced_indent(self, cr, uid, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False
        try:
            dtm = datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_INDENT"+dtm+".csv"
            _logger.info("Opening file '%s' for logging the bounced partner detail."%(fname))
            fl= csv.writer(open(file_head+"/"+fname, 'wb'))
            for ln in  bounced_detail:
                fl.writerow(ln)
            _logger.info("Successfully exported the bounced partner detail to the file %s."%(fname))
            return True
        except Exception, e:
            print e
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False

    def do_import_indent_data(self, cr, uid,ids, context=None):
        
        #file_path = "/home/ara/Desktop/odt/indent/indent20132014.csv"
        #file_path = "/home/ara/Desktop/odt/indent/IDENTNOT20132014BUTPO20132014.csv"
        #file_path = "/home/ara/Desktop/odt/indent/INDENTNOT20132014BUTINWORD20132014.csv"
        
        file_path = "/home/maize/data/2_aug/indent_special.csv"
        if not file_path or file_path == "":
            _logger.warning("Import can not be started. Configure your schedule Actions.")
            return True
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            
        if not data_lines:
            _logger.info("File '%s' has not data or it has been already imported, please update the file."%(file_path))
            return True
        _logger.info("Starting Import Indent Process from file '%s'."%(file_path))
        indent_pool =self.pool.get('indent.indent')
        indent = []
        c_po=[]
        not_po = []
        cn_po=[]
        project_not_match = []
        indent_list = []
        bounced_indent = [tuple(fields)]
        for data in data_lines:
            try:
                    #+++++++++++++++++++++++++++++++++++++++++++++++++++++=======================#
                       
#                 if int(data['PONO'].strip()) != 0:
#                     wf_service = netsvc.LocalService('workflow')
#                     indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"]+'/'+data["INDYEAR"])])[0]
#                     user_indent = self.pool.get('indent.indent').browse(cr,uid,indent).indentor_id.id
#                     wf_service.trg_validate(user_indent, 'indent.indent', indent, 'indent_confirm', cr)
#                     wf_service.trg_validate(7, 'indent.indent', indent, 'indent_inprogress', cr)
#                     c_po.append(data["INDENTNO"])
#                 else:
#                     not_po.append(data["INDENTNO"]+'/'+data["INDYEAR"])
#           except:
#                print "data['INDENTNO']", data['INDENTNO']
#        print ">>>>>>>>>>>>>>>>>>>>>.", not_po
                   
                #==============================================================================#
                fiscalyear = data['INDYEAR'].strip()
                exist_indent_list = indent_pool.search(cr,uid,[('name','=', data["INDYEAR"]+'/'+data["INDENTNO"].strip())])
                exist_indent = []
                if exist_indent_list:
                    exist_indent = exist_indent_list[0]
                if not exist_indent:
                    emp_obj = self.pool.get('hr.employee')
                    if data["INDENTNO"]:
                        name = data["INDYEAR"]+'/'+data["INDENTNO"].strip()
                    indentor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])[0]
                    emp = emp_obj.search(cr, uid, [('user_id', '=', indentor)], context=context)[0]
                       
                    if data["DEPTCODE"].strip():
                        if len(data["DEPTCODE"].strip()) == 1:
                            dept = '00'+data["DEPTCODE"].strip()
                        elif len(data["DEPTCODE"].strip()) == 2:
                            dept = '0'+data["DEPTCODE"].strip()
                        elif len(data["DEPTCODE"].strip()) == 3:
                            dept = data["DEPTCODE"].strip()
                        department = self.pool.get('stock.location').search(cr, uid,[('code','=',dept)])[0]
                           
                    if data["ITEMREQ"] =='U':
                        req = 'urgent'
                    else:
                        req = 'ordinary'
                           
                    if data["INDTYPE"] =='New':
                        type = 'new'
                    else:
                        type = 'existing'
                    if data["ITEMFOR"] =='S':
                        item_for = 'store'
                    else:
                        item_for = 'capital'
                    if data["INDDATE"] == 'NULL' or data["INDDATE"] == '' or data["INDDATE"] == '00:00.0' or data["INDDATE"] == '  ':
                        indent_date = ''
                    else:
                        indent_date=datetime.strptime(data["INDDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                    req_date=''
                    if data["REQDATE"] == 'NULL' or data["REQDATE"] == '' or data["REQDATE"] == '00:00.0' or data["REQDATE"] == '  ':
                        req_date = ''
                    else:
                        req_date = datetime.strptime(data["REQDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                       
                    mach = False
                    if len(data["MACHCODE"].strip()) == 1:
                        mach = '00'+data["MACHCODE"].strip()
                    elif len(data["MACHCODE"].strip()) == 2:
                        mach = '0'+data["MACHCODE"].strip()
                    elif len(data["MACHCODE"].strip()) == 3:
                        mach = data["MACHCODE"].strip()
                    project=False
                    if mach:
                        project = self.pool.get('account.analytic.account').search(cr,uid,[('code','=',mach)])[0]
                           
                    description=data['REMARK1']+'\n'+data['REMARK2']
                    data['indent'] = indent_pool.create(cr, uid, {'name':name,
                                                                  'indentor_id':indentor,
                                                                  'employee_id':emp,
                                                                  'indent_date': indent_date,
                                                                  'requirement': req,
                                                                  'type':type,
                                                                  'department_id': department,
                                                                  'item_for':item_for,
                                                                  'maize':name,
                                                                  'required_date':req_date,
                                                                  'description':description,
                                                                  'fiscalyear':fiscalyear,
                                                                  'analytic_account_id':project
                                                       }, context)
                    indent_list.append(name)
       
   
            except:
                print "data['INDENTNO']", data['INDENTNO']
                cn_po.append(data['INDENTNO'])
                reject = [ data.get(f, '') for f in fields]
                bounced_indent.append(reject)                
                _logger.warning("Skipping Record with Indent code '%s'."%(data['INDENTNO']), exc_info=True)
                continue
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>with po",c_po
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>>>>>with not po",not_po
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>>>>>canvel",cn_po
        print "project_not_match>>>>>>>>>>>>>>>>>",project_not_match
        head, tail = os.path.split(file_path)
        self._write_bounced_indent(cr, uid, head, bounced_indent, context)
        _logger.info("Successfully completed import journal process.")
        
#        for delete blank contract indent
#         con_un = []
#         indent_pool = self.pool.get('indent.indent')
#         contracts=indent_pool.search(cr,uid,[('contract','=',True)])
#         for con in indent_pool.browse(cr,uid,contracts):
#             if not con.product_lines:
#                 con_un.append(con.id)
#         indent_pool.unlink(cr,uid,con_un)

        #validate po contract
#         wf_service = netsvc.LocalService('workflow')
#         contracts = self.pool.get('indent.indent').search(cr,uid,[('contract','=',True)])
#         for co in contracts:
#             user_indent = self.pool.get('indent.indent').browse(cr,uid,co).indentor_id.id
#             wf_service.trg_validate(user_indent, 'indent.indent', co, 'indent_confirm', cr)
#             wf_service.trg_validate(7, 'indent.indent', co, 'indent_inprogress', cr)

         
        
        return True
import_indent_data()
