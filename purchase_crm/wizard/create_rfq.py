# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today Tiny SPRL (<http://tiny.be>).
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
from osv import fields,osv

from tools.translate import _

from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import time

class crm_make_purchase(osv.osv_memory):

    _name = 'crm.make.purchase'
    _description = 'Opportunity To Purchase Quotation'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Supplier', required=True),
        'product_ids': fields.many2many('product.product', 'opportunity_prod_rel', 'opp_id', 'product_id', 'Products', required=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
    }

    def convert_to_rfq(self, cr, uid, ids, context=None):
        """
        This function  Create an Quotation on given opportunity.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created purchase order.
        """
        if context is None:
            context = {}

        case_obj = self.pool.get('crm.lead')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        opp_ids = context and context.get('active_ids', [])

        for opportunity in self.browse(cr, uid, ids, context=context):
            partner = opportunity.partner_id
            partner_addr = partner_obj.address_get(cr, uid, [partner.id], ['default'])
            pricelist = partner.property_product_pricelist_purchase.id
            fpos = partner.property_account_position and partner.property_account_position.id or False
            case = case_obj.browse(cr, uid, opp_ids and opp_ids[0] or [], context=context)
            location_id = self.pool.get('purchase.order').onchange_warehouse_id(cr, uid, [], opportunity.warehouse_id.id)['value']['location_id']
            vals = {
                'origin': _('Opportunity - ID: %s') % str(case.id),
                'section_id': case.section_id and case.section_id.id or False,
                'partner_id': partner.id,
                'partner_address_id':partner_addr['default'],
                'pricelist_id': pricelist,
                'date_order': fields.date.context_today(self,cr,uid,context=context),
                'fiscal_position': fpos,
                'location_id':location_id,
                'warehouse_id':opportunity.warehouse_id.id,
            }
            dt = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            if partner.id:
                vals['user_id'] = partner.user_id and partner.user_id.id or uid
            new_id = purchase_obj.create(cr, uid, vals, context=context)
            case_obj.write(cr, uid, [case.id], {'ref2': 'purchase.order,%s' % new_id})
            for product_id in opportunity.product_ids:
                product = product_obj.browse(cr, uid, product_id.id, context=context)
                res = self.pool.get('purchase.order.line').onchange_product_id(cr, uid, [], pricelist, product.id, 1, product.uom_id.id, partner.id, date_order=dt)
                res = res['value']
                line_vals = {
                    'name': res['name'],
                    'product_id': product.id,
                    'order_id': new_id,
                    'price_unit': res['price_unit'],
                    'date_planned': res['date_planned'],
                    'product_uom':res['product_uom'],
                    'taxes_id': [(6,0,res['taxes_id'])],
                }
                purchase_line_obj.create(cr, uid, line_vals, context=context)

        result = {
            'name': 'Request For Quotation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id': new_id
        }
        return result

crm_make_purchase()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: