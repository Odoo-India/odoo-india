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
    'name' : 'Maize Partner',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 111,
    'category': 'Maize Partner',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Partner',
    'description' : """
""",
    'depends' : ['base', 'maize_product'],
    'data' : [
        'security/ir.model.access.csv',
        'po_series_data.xml',
        'maize_partner_data.xml',
        'maize_partner_view.xml',
        'maize_company_data.xml',
        'wizard/import_customer_data.xml',
        'wizard/account_create_wizard.xml',
    ],
    'update_xml' : [],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
