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
{
    'name' : 'l10n_in_purchase',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 111,
    'category': 'Purchase Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Purchase',
    'description' : """
Managing Purchase.
===================== 

""",
    'depends' : ['purchase'],
    'data' : [
    ],
    'update_xml' : ['l10n_in_purchase_view.xml',
                    'l10n_in_account_view.xml',
                    'purchase_report.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
