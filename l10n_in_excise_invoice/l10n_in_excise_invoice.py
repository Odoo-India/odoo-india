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

from osv import fields, osv

class res_company(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'range': fields.char('Range', size=64),
        'division': fields.char('Division', size=64),
        'commissionerate': fields.char('Commissionerate', size=64),
        'tariff_rate': fields.integer('Tariff Rate'),
    }

res_company()

class res_partner(osv.Model):
    _inherit = "res.partner"

    _columns = {
        'ecc_no' : fields.char('ECC', size=32, help="Excise Control Code"),
    }

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
