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

class stock_gatepass(osv.Model):
    _inherit = 'stock.gatepass'
    
    def onchange_delivery_order(self, cr, uid, ids, order_id=False, *args, **kw):
        result = {'line_ids': []}
        lines = []
 
        if not order_id:
            return {'value': result}
        
        order = self.pool.get('stock.picking.out').browse(cr, uid, order_id)
        products = order.move_lines
        
        for product in products:
            vals = dict(
                product_id = product.product_id.id, 
                product_qty = product.product_qty, 
                uom_id= product.product_uom.id, 
                name = product.product_id.name, 
                location_id = product.location_id.id,
                location_dest_id = product.location_dest_id.id,
                prodlot_id=product.prodlot_id.id
            )
            
            #TODO: need to check in other ways whether sale module is installed or not instead of try and except..
            try:
                if product.sale_line_id:
                    vals['price_unit'] = product.sale_line_id.price_unit
            except:
                vals['price_unit'] = product.product_id.list_price
            lines.append(vals)
        result['line_ids'] = lines
        result['partner_id'] = order.partner_id.id
        return {'value': result}

    _sql_constraints = [
        ('gatepass_delivery_uniq', 'unique(out_picking_id)', 'You can not create multiple Gatepass for same Delivery Order!'),
    ]

stock_gatepass()