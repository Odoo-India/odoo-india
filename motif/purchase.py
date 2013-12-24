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

from openerp.osv import osv,fields
from openerp.tools.translate import _

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'service_order': fields.boolean('Service Order'),
        'workorder_id':  fields.many2one('mrp.production.workcenter.line','Work-Order')
    }

purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'

    def _get_p_uom_id(self, cr, uid, *args):
        cr.execute('select id from product_uom order by id limit 1')
        res = cr.fetchone()
        return res and res[0] or False

    _columns = {
        'line_qty': fields.float('Purchase Quantity'),
        'line_uom_id':  fields.many2one('product.uom','Purchase UoM'),
        'consignment_variation': fields.char('Variation(±)')
    }

    _defaults = {
        'line_uom_id':_get_p_uom_id,
        'consignment_variation':'0.0'
    }

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        onchange handler of product_id.
        """
        prod_obj = self.pool.get('product.product')
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)
        if product_id:
            p = prod_obj.browse(cr, uid, product_id)
            p_qty = res['value'].get('product_qty',0.0)
            res['value'].update({
                        'line_qty': p_qty * p.p_coefficient,
                        'line_uom_id':p.p_uom_id.id
                        })
        return res

    def create(self, cr, uid, vals ,context=None):
        """
            Process
                -Future use
        """
        return super(purchase_order_line,self).create(cr, uid, vals, context=context)


    def add_variations(self, cr, uid, ids ,context=None):
        """
            Process
                -call wizard to add variation on line
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get consume wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'motif', 'view_consignment_variation_po')
        current = self.browse(cr, uid, ids[0], context=context)
        context.update({
                        'uom': current.line_uom_id.name,
                        })
        return {
            'name': _('Add Consignment Variation'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'consignment.variation.po',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }


purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
