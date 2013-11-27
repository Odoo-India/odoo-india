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
    'name' : 'Indent Management',
    'version' : '1.0',
    'author' : 'OpenERP S.A.',
    'sequence': 120,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Manage and track internal material requests',
    'description' : """
Indent Management
================================================================================================================================================================ 
Usually big companies setup and maintain internal requisition to be raised by Engineer, Plant Managers or Authorised Employees. 

Using Indent Management you can control the purchase and issue of material to employees with in company warehouse.

- Indents
- Store purchase
- Capital Purchase
- Project Costing
- Valuation
- Etc
""",
    'depends' : ['stock', 'purchase'],
    'data' : [
        "stock_indent_data.xml",
        "stock_indent_sequence.xml"
    ],
    'update_xml' : [
        'stock_indent_view.xml',
        'stock_indent_workflow.xml',
        'stock_workflow_change.xml',
        'stock_indent_report.xml'
    ],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
