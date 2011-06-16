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
    "name": "Tally Integrator",
    "version": "1.0",
    "author": "OpenERP SA",
    "website": "http://www.openerp.com",
    "category": 'Generic Modules/Accounting',
    "depends": ["base","account_voucher",'account_accountant','multi_company','hr','stock','sale'],
    "description": """
    This module will load the Chart Of account from Tally.
 
    """,
    "init_xml": [],
    "update_xml": ['tally_connection_wizard.xml'
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
