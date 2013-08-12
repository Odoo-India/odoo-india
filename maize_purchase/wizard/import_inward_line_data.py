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
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
import csv
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_inward_line_data(osv.osv_memory):
    _name = "import.inward.line.data"
    
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
    
    def _write_bounced_indent(self, cr, uid, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) Inward line detail to the file. ")
            return False
        try:
            dtm = datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_INWARD_LINE"+dtm+".csv"
            _logger.info("Opening file '%s' for logging the bounced inward line detail."%(fname))
            fl= csv.writer(open(file_head+"/"+fname, 'wb'))
            for ln in  bounced_detail:
                fl.writerow(ln)
            _logger.info("Successfully exported the bounced inward line detail to the file %s."%(fname))
            return True
        except Exception, e:
            print e
            _logger.warning("Can not Export bounced(Rejected) Inward line detail to the file. ")
            return False
    
    def do_import_inward_data(self, cr, uid,ids, context=None):

        file_path = "/home/maize/data/inward/inward_line_after_1_8_2013.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        move_pool =self.pool.get('stock.move')
        picking_obj =self.pool.get('stock.picking')
        picking_in_obj = self.pool.get('stock.picking.in')
        partial_picking_obj =self.pool.get('stock.partial.picking')
        supplier_location = self.pool.get('stock.location').search(cr, uid, [('name','ilike','Suppliers')])
        if not supplier_location:
            raise osv.except_osv(_('Warning!'), _('Please define Supplier location in the database')) 
        indent = []
        rejected =[]
        exist_po = []
        po_picking_key = {}
        po_exist = []
        picking_exist = []
        exist_picking = []
        po_not_found = []
        indent_not_found = []
        bounced_inward = [tuple(fields)]
        i=[]
        m_v=[]
        in_name = []        
        for data in data_lines:
            pp=0
            m=''
            try:
                name = inwrd_num = fiscalyear=''
                if data["ITEMCODE"]:
                    product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                if data["INDENTOR"]:
                    inwrd_num = data["INDENTOR"]
                if data["INDENTNO"]:
                    maize_no = data["INDENTNO"]
                #if data["INWARDNO"]:
                    #search_picking = data["INWARDNO"]
                    #picking_id = self.pool.get('stock.picking').search(cr,1,[('maize_in','=',search_picking)])[0]
                if data["RECVQTY"]:
                    rqty = data["RECVQTY"]
                if data["INWRATE"]:
                    rate = data["INWRATE"]
                if data["POYEAR"]:
                    poyear = data["POYEAR"]
                if data["CHLNQTY"]:
                    chlnqty = data["CHLNQTY"]
                if data["INWYEAR"]:
                    indyear = data["INWYEAR"] 
                if data['INDYEAR']:
                    fiscalyear = data['INDYEAR']
                if data['INWYEAR'] and data['INWARDNO']:
                    maize_in = data['INDYEAR']+'/'+data["INDENTNO"]
                po_name = data['POYEAR']+'/'+data["POSERIES"] +'/'+ data["PONO"]
                maize_name = data['INDYEAR']+'/'+data["INWARDNO"]
                new_picking_id = False
                purchase_date = ''
                date_start = self._get_start_end_date_from_year(cr,uid,indyear)['start']
                date_end = self._get_start_end_date_from_year(cr,uid,indyear)['end']
                date_start_po = self._get_start_end_date_from_year(cr,uid,poyear)['start']
                date_end_po = self._get_start_end_date_from_year(cr,uid,poyear)['end']

                indent_id=False
                indentor_id=False
                #fiscalyear = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',data['INDYEAR'].strip())])
                if data["INDENTNO"] and fiscalyear:
                    try:
                        indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data['INDYEAR']+'/'+data["INDENTNO"])])
                        indent_id = indent and indent[0] or False 
                    except:
                        indent_not_found.append(data['INDYEAR']+'/'+data["INDENTNO"])
                    
                if data["INDENTOR"]:
                    indentor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])
                    indentor_id = indentor and indentor[0] or ''

                
                if po_name:
                    purchase_id = self.pool.get('purchase.order').search(cr,uid,[('maize','=',po_name)])[0]
                    if purchase_id:
                        try:
                            wf_service = netsvc.LocalService('workflow')
                            wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', cr)
                            inward_id = picking_in_obj.search(cr,uid,[('purchase_id','=',purchase_id), ('state','=','assigned')])
                            inwrite = picking_in_obj.write(cr,uid,inward_id[-1],{'maize_in':maize_name})
                            if inward_id[0] not in i:
                                i.append(inward_id[0])
                            if maize_name not in in_name:
                                in_name.append(maize_name)
                            department_id = False
                            if indent_id:
                                department_id = self.pool.get('indent.indent').read(cr,uid,indent_id,['department_id'])['department_id'][0]
                            move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', inward_id[-1]), ('type', '=', 'in'),('product_id', '=', product),('indent', '=', indent_id),('indentor', '=', indentor_id)])
                            m_v.append((0,0,{
                                        'product_id': product,
                                        'quantity':float(chlnqty),
                                        'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                        'location_id': supplier_location[0],
                                        'location_dest_id': 299,#input location fix
                                        'move_id':move_ids[0],
                                        }))
                            print "ward data in", in_name, in_name[0], in_name[-1]
                            if i[0] != i[-1] or len(i)!=1 or in_name[0]!=in_name[-1] or len(in_name)!=1:
                                context.update({'active_model': 'stock.picking', 'active_id':i[0], 'active_ids': [i[0]],'default_type':'in'})
                                if len(i)!=0:
                                    m_v.pop()
                                print "\n>>>>>>>>>>> new picking create>>>>>>>>>>>", m_v, i[0]
                                partial_id = partial_picking_obj.create(cr, uid, {'date': datetime.today(), 'picking_id': i[0], 'move_ids': m_v})
                                res = partial_picking_obj.do_partial(cr, uid,[partial_id],context)
                                i.remove(i[0])
                                in_name.remove(in_name[0])
                                m_v=[]
                                pp=1
                            if inward_id:
                                if pp==1 or len(i)!=1:
                                    #move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', inward_id[-1]), ('type', '=', 'in'),('product_id', '=', product),('indentor_id', '=', indentor_id)])
                                    m_v.append((0,0,{
                                            'product_id': product,
                                            'quantity':float(chlnqty),
                                            'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                            'location_id': supplier_location[0],
                                            'location_dest_id': 299,#input location fix
                                            'move_id':move_ids[0],
                                            }))                                  
                                purchase_date = self.pool.get('purchase.order').browse(cr,uid,purchase_id).date_order
                                new_vals = {
                                        'product_id': product,
                                        'quantity':float(chlnqty),
                                        'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                        'location_id': supplier_location[0],
                                        'location_dest_id': 299,#input location fix
                                        'move_id':move_ids[0],
                                        }
                                print ">>>>>>>>>>>>>>>>move>>>>>>>>>>>>>>>>>", move_ids
                                move_pool.write(cr, uid, move_ids[0],{'challan_qty': float(chlnqty)}, context)
                            else:
                                print "\n\n=-=-=- not found line"
                                rejected.append(data['INWARDNO'])
                                reject = [ data.get(f, '') for f in fields]
                                bounced_inward.append(reject)
                        except:
                            po_not_found.append(data["POSERIES"]+'/'+data["PONO"]+'/'+data["POYEAR"])
                            rejected.append(data['INWARDNO'])
                            reject = [ data.get(f, '') for f in fields]
                            bounced_inward.append(reject)
            except:
                rejected.append(data['INWARDNO'])
                reject = [ data.get(f, '') for f in fields]
                bounced_inward.append(reject)
                _logger.warning("Skipping Record with Inward code '%s'."%(data['INWARDNO']), exc_info=True)
                continue
        print "inward_idinward_id>>>", inward_id,maize_name
        print "rejectedrejectedrejected", rejected
        print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", po_not_found
        #print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", indent_not_found
        head, tail = os.path.split(file_path)
        self._write_bounced_indent(cr, uid, head, bounced_inward, context)
        _logger.info("Successfully completed import Inward process.")
        return True
    
import_inward_line_data()
