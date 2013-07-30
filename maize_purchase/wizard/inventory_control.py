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

from openerp.osv import fields, osv
from openerp.tools.translate import _

class inventory_control(osv.osv_memory):
    
    _name = 'inventory.control'
    
    _columns = {
            'select_query': fields.selection(
                                             [
                                              ('po', 'PO'), 
                                              ('pending_po', 'Pending PO'), 
                                              ('inward', 'Inward'), 
                                              ('bill', 'Bill'),
                                             ], 'Select Query'),
            'supplier_from_id': fields.many2one('res.partner', 'Supplier From'),
            'supplier_to_id': fields.many2one('res.partner', 'Supplier To'),
            'item_code_from_id': fields.many2one('product.product', 'Item Code From'),
            'item_code_to_id': fields.many2one('product.product', 'Item Code To'),
            'po_series_id': fields.many2one('product.order.series', 'PO Series'),
#            'number_from':
#            'number_from':   
            'date_from': fields.date('Date From'),
            'date_to': fields.date('Date To')
        }
    
    def get_data(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')
        read_rec = self.read(cr, uid, ids[0], context=context)
        browse_rec = self.browse(cr, uid, ids[0], context=context)
        select_query = browse_rec.select_query
        supplier_code_from = browse_rec.supplier_from_id.supp_code
        supplier_code_to = browse_rec.supplier_to_id.supp_code 
        item_code_from = browse_rec.item_code_from_id.default_code 
        item_code_to = browse_rec.item_code_to_id.default_code 
        date_from = browse_rec.date_from 
        date_to = browse_rec.date_to 
        po_series_id = browse_rec.po_series_id.id
        
        if supplier_code_from and not supplier_code_to or supplier_code_to and not supplier_code_from:
            raise osv.except_osv(_("Warning !"), _("Enter values in both Supplier From and Supplier To."))
        
        if item_code_from and not item_code_to or item_code_to and not item_code_from:
            raise osv.except_osv(_("Warning !"), _("Enter values in both Item Code From and Item Code To."))
        
        if date_from and not date_to or date_to and not date_from:
            raise osv.except_osv(_("Warning !"), _("Enter values in both Date From and Date To."))
        
        if str(supplier_code_from) > str(supplier_code_to):
            raise osv.except_osv(_("Warning !"), _("Supplier To Code should be greater than Supplier From Code."))
        
        if str(item_code_from) > str(item_code_to):
            raise osv.except_osv(_("Warning !"), _("Item Code To should be greater than Item Code From."))
        
        if date_from > date_to:
            raise osv.except_osv(_("Warning !"), _("Date To should be greater than Date From."))
        
        action_model, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'maize_purchase', 'action_purchase_order_info_report'))
        
        action = self.pool.get(action_model).read(cr, uid, action_id, context=context)
        
        domain = [
                  ('date', '>=', date_from),
                  ('date', '<=', date_to), 
                  ('po_series_id', '=', po_series_id), 
                  ('default_code', '>=', item_code_from),
                  ('default_code', '<=', item_code_to), 
                  ('supplier_code', '>=', supplier_code_from),
                  ('supplier_code', '<=', supplier_code_to)
                 ]
        
        new_domain = []
        for d in domain:
            if not (d[2] is None or d[2] is False):
                new_domain.append(d)
                
        action['domain'] = new_domain
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
