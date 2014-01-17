# -*- encoding: utf-8 -*-
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
    "name" : "Bill Order Reference",
    "version" : "1.0",
    "depends" : [
        "stock",
        "account",
    ],
    'author' : 'OpenERP SA',
    "description": """
Customized Invoice Form
====================================================== 
Fields added on Invoice: Buyer Order No, Bill of Entry, Address, Delivery Date.
While creating invoice from picking the entries will be filled on invoice form.
    """,
    'website' : 'http://www.openerp.com',
    "category" : "Accounting & Finance",
    "update_xml" : [
       "invoice_buyer_reference_view.xml"
    ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: