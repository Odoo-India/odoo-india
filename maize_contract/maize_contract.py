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

import time
from datetime import datetime
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class indent_indent(osv.Model):
    _inherit = 'indent.indent'
    _columns = {
        'contract': fields.boolean('Contract', help="Check box True means the contract otherwise it is indent", readonly=True)
        }
    
    _defaults = {
        'contract': False
        }
    
indent_indent()

class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    
    def onchange_compute_days(self, cr, uid, ids, date_start, date_end, context=None):
        res = {}
        for po in self.browse(cr, uid, ids, context=context):
            day = po.no_of_days
            if date_start and date_end:
                day_from = datetime.strptime(date_start,"%Y-%m-%d")
                day_to = datetime.strptime(date_end,"%Y-%m-%d")
                day += (day_to - day_from).days + 1
                res['no_of_days'] = day
            elif po.extended_date_from1 and po.extended_date_to1:
                res = self.onchange_compute_days(cr, uid, ids, po.extended_date_from1, po.extended_date_to1)
                res['value']['no_of_days'] = po.no_of_days
            elif po.date_from and po.date_to:
                res = self.onchange_compute_days(cr, uid, ids, po.date_from, po.date_to, {'start': True})
                res['value']['no_of_days'] = po.no_of_days
                return res
        return {'value' : res}
    
    _columns = {
        'contract': fields.related('indent_id', 'contract', type='boolean', relation='indent.indent', string='Contract', store=True, readonly=True),
        'no_of_days': fields.integer("No of Days", help="Calculate number of days for contracts"),
        'date_from': fields.date('From Date', required=True),
        'date_to': fields.date('To Date'),
        'extended_date_from1': fields.date('Extended From'),
        'extended_date_from2': fields.date('Extended From'),
        'extended_date_to1': fields.date('Extended Upto'),
        'extended_date_to2': fields.date('Extended Upto'),
        }
    
    _defaults = {
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'date_to': lambda *a: datetime.now().strftime('%Y-%m-%d'), 
        }