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
    'name' : 'Gate Pass',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Gate Passes',
    'description' : """
Gate Pass
===========
* Document that allows gate keeper to pass the outgoing material, products, etc.
* Supports returnable and non returnable gate pass, Track returning items automatically
* Report that allows you to track the pending gate pass
""",
    'depends' : ['stock'],
    'data' : [
        'stock_gatepass_sequence.xml',
        'stock_gatepass_data.xml',
    ],
    'update_xml' : [
        'stock_gatepass_view.xml',
        'stock_gatepass_workflow.xml',
        'stock_gatepass_report.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
