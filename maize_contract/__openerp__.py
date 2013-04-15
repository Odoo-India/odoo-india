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
    'name' : 'Maize Contract',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Contract',
    'description' : """
The user will create an contract 
================================================================================================================================================================ 
""",
    'depends' : ['indent'],
    'data' : [
        'security/ir.model.access.csv',
        'contract_data.xml',
        'maize_contract_sequence.xml',
        'contract_report.xml',
        'maize_contract_view.xml',
        'report/indent_report_view.xml',
        'report/indent_purchase_report_view.xml',
    ],
    'update_xml' : [],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
