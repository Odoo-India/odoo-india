# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'service_after_sales': fields.boolean('Service After Sales', help="Tick if you want to create contract to manage sales after service."),
    }

product_template()

class account_analytic_account(osv.osv):
    _name = "account.analytic.account"
    _inherit = "account.analytic.account"
    
    _columns = {
        'sale_id': fields.many2one('sale.order', string="Sales Order", readonly=True),
        'delivery_id': fields.many2one('stock.picking.out', string="Delivery Order", readonly=True),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({'sale_id' : False})
        default.update({'delivery_id' : False})
        return super(account_analytic_account, self).copy(cr, uid, id, default, context)

account_analytic_account()

class stock_partial_picking(osv.osv):
    _inherit = 'stock.partial.picking'

    def do_partial(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        prod_pool = self.pool.get('product.product')
        cont_pool = self.pool.get('account.analytic.account')
        stock_pool = self.pool.get('stock.picking.out')
        prodlot_obj = self.pool.get('stock.production.lot')
        picking_obj = self.browse(cr, uid, ids[0], context=context)
        delivery_id = context.get('active_id', False)
        if not delivery_id:
            return super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        delivery_order = stock_pool.browse(cr, uid, [delivery_id], context=context)[0]
        picking_type = picking_obj.picking_id.type
        manager_id = False

        if not (picking_type == 'out'):
            return super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        if delivery_order.sale_id:
            if delivery_order.sale_id.section_id and delivery_order.sale_id.section_id.user_id:
                manager_id =  delivery_order.sale_id.section_id.user_id.id
            else:
                manager_id = delivery_order.sale_id.user_id.id

        for wizard_line in picking_obj.move_ids:
            prod_obj = prod_pool.browse(cr, uid, [wizard_line.product_id.id], context=context)[0]
            if prod_obj.service_after_sales and wizard_line.prodlot_id:
                vals = {'name' : wizard_line.product_id.name + ' (%s)' % wizard_line.prodlot_id.name ,
                        'code': wizard_line.prodlot_id.name,
                        'type' : 'contract',
                        'partner_id': delivery_order.partner_id and delivery_order.partner_id.id or False,
                        'date_start' : time.strftime('%Y-%m-%d'),
                        'company_id' : delivery_order.company_id.id,
                        'manager_id' : manager_id,
                        'sale_id' : delivery_order.sale_id.id,
                        'delivery_id' : delivery_id or False
                 }
                contract_id = cont_pool.create(cr, uid, vals, context=context)
                prodlot_obj.write(cr, uid, [wizard_line.prodlot_id.id], {'contract_id' : contract_id}, context=context)
        return super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)

stock_partial_picking()

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    
    _columns = {
        'contract_id': fields.many2one('account.analytic.account', string="Contract", readonly=True, help="Reference of Contract which has generated after sales."),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({'contract_id' : False})
        return super(stock_production_lot, self).copy(cr, uid, id, default, context)
    
stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
