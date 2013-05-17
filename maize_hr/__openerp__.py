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
    'name' : 'Maize Human Resources',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Human Resources Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Maize Human Resources',
    'description' : """
This module inherits the base hr module which maintains some Human Resources data.
================================================================================================================================================================ 
""",
    'depends' : ['hr'],
    'data' : [
            'maize_hr_view.xml',
            'wizard/import_hr_view.xml',
            'security/ir.model.access.csv'
    ],
    'update_xml' : [],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
