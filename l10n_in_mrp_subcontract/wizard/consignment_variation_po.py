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
import openerp.addons.decimal_precision as dp

class consignment_variation_po(osv.osv_memory):
    _name = "consignment.variation.po"
    _description = "Consignment Variation"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -To set default value
        """
        context = context or {}
        res = {}
        uom = context and context.get('uom', False) or False
        if 'uom' in fields:
            res.update({'uom': uom})
        if 'sign' in fields:
            res.update({'sign': '+'})
        if 'variation' in fields:
            res.update({'variation': 0.0})
        return res

    _columns = {
        'sign':fields.selection([('+','+'),('-','-')], 'Sign', required=True),
        'variation': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'uom':fields.char('Purchase UoM', readonly=True),
    }


    def to_update(self, cr, uid, ids, context=None):
        """
        - Process
            - update variation on lines, just for only information purpose
        """
        context = context or {}
        order_line_obj = self.pool.get('purchase.order.line')

        wizard_rec = self.browse(cr, uid, ids[0])
        line_id = context and context.get('active_id', False) or False
        to_write = str(wizard_rec.sign)+' '+ str(wizard_rec.variation)+' ' + str(wizard_rec.uom) 
        if line_id:
            order_line_obj.write(cr ,uid, line_id, {'consignment_variation': to_write})
        return True

consignment_variation_po()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
