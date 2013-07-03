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
from osv import fields, osv

class update_excise(osv.TransientModel):
    _name = "update.excise"
    _description = "Update Excise"

    def update_excise_amount(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        taxes = self.browse(cr, uid, ids[0], context=context)
        vals = {
            'excies_ids': [(6, 0, [excise.id for excise in taxes.excise_ids])]
        }
        self.pool.get('purchase.order').write(cr, uid, context.get('active_ids', []), vals, context=context)
        return True

    _columns = {
        'packing_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('per_unit', 'Per Unit'), ('include', 'Include in price')], 'Packing & Forwarding Type'),
        'package_and_forwording': fields.float('Packing & Forwarding'),
        'commission': fields.float('Commission'),
        'excise_ids': fields.many2many('account.tax', 'update_excise_tax', 'update_tax_id', 'tax_id', 'Excise'),
        'vat_ids': fields.many2many('account.tax', 'update_vat_tax', 'update_tax_id', 'tax_id', 'VAT'),
        'insurance_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Insurance Type'),
        'insurance': fields.float('Insurance'),
        'freight_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('per_unit', 'Per Unit'), ('extra', 'EXTRA'),('include', 'Include in price')], 'Freight Type'),
        'freight': fields.float('Freight'),
        'other_discount': fields.float('Discount / Round Off'),
        'discount_percentage':  fields.float('Discount (%)'),
        'other_tax_ids': fields.many2many('account.tax', 'update_other_tax', 'update_tax_id', 'tax_id', 'Other Tax'),
    }

update_excise()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
