# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv,fields

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
        'city_id': fields.many2one('res.city', 'City')
    }

    def onchange_city(self, cr, uid, ids, city_id, context=None):
        if not city_id:
            return {'value': {}}
        city = self.pool.get('res.city').browse(cr, uid, city_id, context=context)
        return {'value': {'state_id': city.state_id.id, 'city': city.name}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
