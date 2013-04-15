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
    'name' : 'Indent',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Indent',
    'description' : """
The user will raise an indent form to the stores, The store keeper checks for the availability, if available issue the material else raise purchase requisition.
================================================================================================================================================================ 
""",
    'depends' : ['purchase_requisition', 'hr'],
    'data' : [
        'indent_view.xml',
        'indent_data.xml',
        'indent_workflow.xml',
        'stock_workflow.xml',
        'indent_sequence.xml',
        'purchase_report.xml',
        'report/indent_report_view.xml',
        'report/indent_purchase_report_view.xml',
    ],
    'update_xml' : ['security/ir.model.access.csv', 'security/indent_security.xml'],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
