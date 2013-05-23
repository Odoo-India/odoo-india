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

from openerp.osv import fields, osv

class stock_picking_out(osv.osv):
    
    _inherit = 'stock.picking.out'
    
    def _get_tax_names(self, cr, uid, ids, context=None):
        invoice_tax_obj = self.pool.get('account.invoice.tax')
        tax_rate_value = []
        invoice_obj = self.pool.get('account.invoice')
        invoice_id = self.browse(cr, uid, ids[0], context=context).sale_id.invoice_id.id
        taxes = invoice_obj.browse(cr, uid, invoice_id, context=context).tax_line
        for tax in taxes:
            if invoice_tax_obj.browse(cr, uid, tax.id, context=context).tax_categ == 'cst':
                name = invoice_tax_obj.browse(cr, uid, tax.id, context=context).name
                tax_rate_value.append(name)
                amount = invoice_tax_obj.browse(cr, uid, tax.id, context=context).amount
                tax_rate_value.append(amount)
                return tax_rate_value
        return ['', '']
    
    def _get_tot_qty(self, cr, uid, ids, context=None):
        qty = 0
        for move in self.browse(cr, uid, ids[0], context=context).move_lines:
            qty += move.product_qty
        return qty
    
class res_company(osv.osv):
    
    _inherit = 'res.company'
    
    _columns = {
        'transporters_name': fields.char('Transporters Name', size=64),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
