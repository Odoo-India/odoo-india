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
    'name' : 'Quotation Template',
    'version' : '1.0',
    'author' : 'OpenERP S.A.',
    'sequence': 120,
    'category': 'Sales Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Quotation Template',
    'description' : """
Prepare and propose quotations to your customers quickly!
============================================================
This module helps you to create quotations quickly and easily by using pre-defined templates for quotations.

Key Features
++++++++++++++++++
The sales manager can prepare quotation templates for products and services, define discount etc. and a sales person can just select template while creating quotations.

* Create quotations quickly
* Provide Discounts on Templates
* Use different Pricelists and Currencies

Video Tutorial: http://www.youtube.com/watch?v=PTy3TOH9tQM


""",
    'depends' : ['sale'],
    'data' : [
    ],
    'update_xml' : [
        'quotation_template_view.xml',
    ],

    'demo': [
    ],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

