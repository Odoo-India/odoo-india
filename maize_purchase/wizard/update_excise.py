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

class update_excise(osv.osv_memory):
    _name = "update.excise"
    _description = "Update Excise"

    def update_excise_amount(self, cr, uid, ids, context=None):
        return True

    _columns = {
        'excise_ids': fields.many2many('account.tax', 'update_excise_excise', 'excise_id', 'tax_id', 'Excise'),
    }

update_excise()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
