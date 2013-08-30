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
import collections
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_inward_line_data(osv.osv_memory):
    _name = "import.inward.line.data"
    _columns = {
       'file_path': fields.char('File Path', required=True, size=256),
    }
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
        data = self.read(cr, uid, ids)[0]
        file_path = data['file_path']
        #file_path = "/home/maize/data/inward/inward_line_20132014.csv"
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
        h=0
        chl=0.0
        ind_lst = []
        chl_lst =[]
        f=0
        maize_in_lst = []
        openerp_name = []
        inc=0
        pp=0
        for data in data_lines:
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
                    chlnqty = float(data["CHLNQTY"])
                if data["INWYEAR"]:
                    indyear = data["INWYEAR"] 
                if data['INDYEAR']:
                    fiscalyear = data['INDYEAR']
                if data['INWYEAR'] and data['INWARDNO']:
                    maize_in = data['INWYEAR']+'/'+data["INWARDNO"]
                po_name = data['POYEAR']+'/'+data["POSERIES"] +'/'+ data["PONO"]
                maize_name = data['POYEAR']+'/'+data["POSERIES"] +'/'+ data["PONO"]+'/'+data['INWYEAR']+'/'+data["INWARDNO"]
                purchase_date = ''

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
                flg=0
                if po_name:
                    purchase_id = self.pool.get('purchase.order').search(cr,uid,[('maize','=',po_name)])[0]
                    #maize_in_lst.append(data['INWYEAR']+'/'+data["INWARDNO"])
                    op_name = data['INWYEAR']+'/'+'IN'+'/'+data["INWARDNO"].zfill(5)
                    if purchase_id:
                        wf_service = netsvc.LocalService('workflow')
                        aa = wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', cr)
                        inward_id = picking_in_obj.search(cr,uid,[('purchase_id','=',purchase_id), ('state','=','assigned')])
                        in_name.append(maize_name)
                        i.append(inward_id[0])
                        if op_name not in openerp_name:
                            openerp_name.append(op_name)
                        elif h==1:
                            if in_name[-1]!=in_name[-2]:
                                inc+=1
                                openerp_name.append(op_name+'new'+str(inc))
                        maize_name_op =  data['INWYEAR']+'/'+data["INWARDNO"]
                        
                        if maize_name_op not in maize_in_lst:
                            maize_in_lst.append(maize_name_op)
                        elif h==1:
                            if in_name[-1]!=in_name[-2]:
                                maize_in_lst.append(maize_name_op)
                        department_id = False
                        if indent_id:
                            department_id = self.pool.get('indent.indent').read(cr,uid,indent_id,['department_id'])['department_id'][0]
                        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', inward_id[-1]), ('type', '=', 'in'),('product_id', '=', product),('indent', '=', indent_id)])
                        ind_lst.append(maize_no)
                        chl_lst.append(chlnqty)
                        m_v.append((0,0,{
                                    'product_id': product,
                                    'quantity':chlnqty,
                                    'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                    'location_id': supplier_location[0],
                                    'location_dest_id': 299,#input location fix
                                    'move_id':move_ids[0],
                                    }))
                        if h==1:
                            context.update({'active_model': 'stock.picking', 'active_id':i[-1], 'active_ids': [i[-1]],'default_type':'in'})
                            if len(i)!=0:
                                aa = m_v.pop()
                                print "aa", aa
                            if i[0]!=i[-1] and in_name[-1]!=in_name[-2]: #add condition for same inward but diffrent po and pon[-1]!=pon[-2]
                                partial_id = partial_picking_obj.create(cr, uid, {'date': datetime.today(), 'picking_id': i[0], 'move_ids': m_v})
                                res = partial_picking_obj.do_partial(cr, uid,[partial_id],context)
                                picking_in_obj.write(cr,uid,res[i[0]]['delivered_picking'],{'maize_in':maize_in_lst[-2],'name':openerp_name[-2]})
                                m_v=[]
                                print "m_vm_vm_vm_vv", m_v
                            elif in_name[-1]!=in_name[-2]:
                                partial_id = partial_picking_obj.create(cr, uid, {'date': datetime.today(), 'picking_id': i[-1], 'move_ids': m_v})
                                res = partial_picking_obj.do_partial(cr, uid,[partial_id],context)
                                picking_in_obj.write(cr,uid,res[i[-1]]['delivered_picking'],{'maize_in':maize_in_lst[-2],'name':openerp_name[-2]})
                                m_v=[]
                            pp=1
                            i.remove(i[0])
                            in_name.remove(in_name[0])
                        h=1
                        if inward_id:
                            if pp==1:
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
                            move_pool.write(cr, uid, move_ids[0],{'challan_qty': float(chlnqty)}, context)
                            
                        else:
                            print "\n\n=-=-=- not found line"
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
        print "rejectedrejectedrejected", rejected,
        print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", po_not_found
        #print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", indent_not_found
        head, tail = os.path.split(file_path)
        self._write_bounced_indent(cr, uid, head, bounced_inward, context)
        _logger.info("Successfully completed import Inward process.")

    #print l
        return True
    
import_inward_line_data()
