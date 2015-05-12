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

{
    'name': 'Indian Nationalized Banks (Unsupported)',
    'version': '1.0',
    'category': 'Indian Localization',
    'summary':'List of All Indian Nationalized Banks',
    'description': """
Indian Nationalized Banks and Bank Account types
==================================================
This module contains list of all Indian Nationalized Banks and Bank Account types.

In order to work with Indian Localization, these module eases the effort to manually create Nationalized banks and bank account types in India.

This module was developed by TinyERP Private Limited (OpenERP India), not supported under any contracts by OpenERP SA or TinyERP.
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['base'],
    'data': ['l10n_in_bank_data.xml'],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
