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

class ir_ui_menu(osv.osv):
    _inherit = 'ir.ui.menu'
    def _get_one_full_name(self, elmt, level=6):
        if level<=0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name(elmt.parent_id, level-1) + "/"
        else:
            parent_path = ''
        if elmt.shortcut_hint:
            return parent_path + elmt.shortcut_hint
        else:
            return parent_path + elmt.name
    def _get_full_name2(self, cr, uid, ids, name=None, args=None, context=None):
        if context is None:
            context = {}
        res = {}
        for elmt in self.browse(cr, uid, ids, context=context):
            res[elmt.id] = self._get_one_full_name2(elmt)
        return res
    def _get_one_full_name2(self, elmt, level=6):
        if level<=0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name2(elmt.parent_id, level-1) + "/"
        else:
            parent_path = ''
        return parent_path + elmt.name
    _columns = {
                'shortcut_hint':fields.char("Search Hint", size=64),
                'complete_name2': fields.function(_get_full_name2, string='Full Path', type='char', size=128),
    }

ir_ui_menu()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
