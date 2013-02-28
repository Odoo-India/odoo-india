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

class comparison_report(osv.osv_memory):
    _name = 'comparison.report'
    _description = 'Comparison for supplier rate'
    _columns = {
        'discount': fields.boolean('Discount'),
        'package_and_forwording': fields.boolean('Packing & Forwarding'),
        'insurance': fields.boolean('Insurance'),
        'commission': fields.boolean('Commission'),
        'other_charge': fields.boolean('Other Charge'),
        'other_discount': fields.boolean('Other Discount'),
        'octroi': fields.boolean('Octroi'),
        'delivey': fields.boolean('Ex. GoDown / Mill Delivey'),
                }
    
    def action_print(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        flage = False
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['discount',  'package_and_forwording',  'insurance', 'commission', 'other_charge', 'other_discount',  'octroi',  'delivey'], context=context)[0]
        report_name = 'Rate_Comparison'
        for value in ['discount',  'package_and_forwording',  'insurance', 'commission', 'other_charge', 'other_discount',  'octroi',  'delivey']:
            if data['form'][value] == True:
                flage = True
        if not flage:
            raise osv.except_osv(_("Warning !"), _("Please check at least one for comparison."))
        return {'type': 'ir.actions.report.xml', 'report_name': report_name, 'datas': data}
comparison_report()