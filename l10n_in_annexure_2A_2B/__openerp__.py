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

{
    'name' : 'Annexure 2A/2B',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 120,
    'category': 'Indian Localization',
    'website' : 'http://www.openerp.com',
    'summary' : 'Annexure 2A/2B',
    'description' : """
Annexure 2A is the Summary of DVAT-30 (Purchases), and Annexure 2B is the Summary of DVAT-31 (Sales).
=====================================================================================================
""",
    'depends' : ['l10n_in_base', 'l10n_in_account_tax', 'sale', 'purchase'],
    'data' : [
    ],
    'update_xml' : [
        'report/annexure_2b_report_view.xml',
    ],

    'demo': [
    ],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
