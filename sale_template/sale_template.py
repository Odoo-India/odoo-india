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

class sale_order(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'is_template': fields.boolean('Template'),
        'template_id': fields.many2one('sale.order', 'Template', domain=[('is_template', '=', True)]),
    }

    def onchange_template(self, cr, uid, ids, template=False):
        result = {'order_line': []}
        lines = []
 
        if not template:
            return {'value': result}

        template = self.browse(cr, uid, template)
        order_lines = template.order_line
        for line in order_lines:
            vals = dict(
                product_id = line.product_id and line.product_id.id or False,
                product_uom_qty = line.product_uom_qty, 
                product_uom = line.product_uom and line.product_uom.id or False,
                product_uos_qty = line.product_uos_qty,
                product_uos = line.product_uos and line.product_uos.id or False,
                price_unit = line.price_unit,
                discount = line.discount,
                name = line.name,
                type = line.type,
                address_allotment_id = line.address_allotment_id and line.address_allotment_id.id or False,
                th_weight = line.th_weight,
            )
            lines.append(vals)
        result['order_line'] = lines
        return {'value': result}

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
