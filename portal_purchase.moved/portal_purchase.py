# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2012 OpenERP S.A. <http://openerp.com>
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

from openerp.osv import osv, fields
import time

class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    def on_change_requisition(self, cr, uid, ids, requisition_id, context=None):
        list_lines = []
        result = {'value': {}}
        req_obj = self.pool.get('purchase.requisition')

        data = req_obj.browse(cr, uid, requisition_id)

        for line in data.line_ids:
            list_lines.append({'product_id': line.product_id.id or False,
                               'product_qty': line.product_qty or 0,
                               'name': line.product_id.name,
                               'product_uom': line.product_uom_id.id,
                               'date_planned': time.strftime('%Y-%m-%d')
                            })

        result['value']['order_line'] = list_lines

        return result

    _defaults = {
        'partner_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).partner_id.id or False,
    }





