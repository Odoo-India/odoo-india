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

class sale_order(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'is_template': fields.boolean('Template'),
        'template_id': fields.many2one('sale.order', 'Offer', domain=[('is_template', '=', True)]),
    }

    def onchange_template(self, cr, uid, ids, template=False, partner_id=False, pricelist_id=False, fiscal_position=False):
        line_obj = self.pool.get('sale.order.line')
        result = {'order_line': []}
        lines = []
 
        if not template:
            return {'value': result}

        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a template,\n select a customer in the template form.'))
        
        template = self.browse(cr, uid, template)
        order_lines = template.order_line
        for line in order_lines:
            vals = line_obj.product_id_change(cr, uid, [],
                pricelist = pricelist_id,
                product = line.product_id and line.product_id.id or False,
                qty = 0.0,
                uom = False,
                qty_uos = 0.0,
                uos = False,
                name = '',
                partner_id = partner_id,
                lang = False,
                update_tax = True,
                date_order = False,
                packaging = False,
                fiscal_position = fiscal_position,
                flag = False)
            vals['value']['discount'] = line.discount
            vals['value']['product_id'] = line.product_id and line.product_id.id or False
            vals['value']['state'] = 'draft'
            vals['value']['product_uom_qty'] = line.product_uom_qty
            vals['value']['product_uom'] = line.product_uom and line.product_uom.id or False
            lines.append(vals['value'])
        result['order_line'] = lines
        result['note'] = template.note
        return {'value': result}

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
