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

class product_product(osv.Model):
    _inherit = 'product.product'

    _columns = {
        'return_container': fields.boolean('Return Container'),
        'product_container_id': fields.many2one('product.product', 'Container'),
    }

product_product()

class stock_move(osv.Model):
    _inherit = 'stock.move'

    def write(self, cr, uid, ids, vals, context=None):
        prodlot_obj = self.pool.get('stock.production.lot')
        if vals.get('prodlot_id'):
            prodlot = prodlot_obj.browse(cr, uid, vals.get('prodlot_id'), context=context)
            if prodlot.product_id and prodlot.product_id.return_container and prodlot.product_id.product_container_id:
                default = dict(product_id = prodlot.product_id.product_container_id.id)
                new_prodlot = prodlot_obj.copy(cr, uid, vals.get('prodlot_id'), default, context=context)
                default = dict(product_id = prodlot.product_id.product_container_id.id, product_uom = prodlot.product_id.product_container_id.uom_id.id, product_qty = 1, prodlot_id = new_prodlot, state = 'assigned')
                [self.copy(cr, uid, id, default, context=context) for id in ids]
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
