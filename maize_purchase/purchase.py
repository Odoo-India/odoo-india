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

import datetime
from openerp.osv import fields, osv

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'
    _columns = {
        'discount': fields.float('Discount'),
                }
purchase_order_line()

class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    _columns = {
        'package_and_forwording': fields.float('Packing & Forwarding'),
        'insurance': fields.float('Insurance'),
        'commission': fields.float('Commission'),
        'other_charge': fields.float('Other Charges'),
        'other_discount': fields.float('Other Discount'),
        'octroi': fields.float('Octroi'),
        'delivey': fields.char('Ex. GoDown / Mill Delivey',size=50),
        'last_po_series': fields.many2one('product.order.series', 'PO Series'),
                }

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        for po in self.browse(cr, uid, ids, context=context):
            
            if po.requisition_id and (po.requisition_id.exclusive=='exclusive'):
                for order in po.requisition_id.purchase_ids:
                    suppler = order.partner_id.id
                    if order.id != po.id:
                        proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
                        if proc_ids and po.state=='confirmed':
                            proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'purchase.order', order.id, 'purchase_cancel', cr)
                    po.requisition_id.tender_done(context=context)
                for line in po.requisition_id.line_ids:
                    today = datetime.datetime.today()
                    year = datetime.datetime.today().year
                    month = datetime.datetime.today().month
                    if month<4:
                        po_year=str(datetime.datetime.today().year-1)+'-'+str(datetime.datetime.today().year)
                    else:
                        po_year=str(datetime.datetime.today().year)+'-'+str(datetime.datetime.today().year+1)
                    self.pool.get('product.product').write(cr,uid,line.product_id.id,{'last_supplier_code':suppler,'last_po_date':today.strftime("%Y-%m-%d"),'last_po_year':po_year},context=context)
        return res    
purchase_order()