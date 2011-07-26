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
    "name": "Easy Tracking",
    "version": "1.1",
    "author": "OpenERP SA",
    "category": "Generic Modules/Human Resources",
    "website": "http://www.openerp.com",
    "description": """
        This Module will provide easy interface to make quick time sheet entry based on project
        It will provide list of projects where the selected user is a member and user can make timesheet entry for a selected week.
            """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ['hr_timesheet', 'project'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'wizard/easy_tracking_current_user_view.xml',
        'hr_timesheet_direct_entry_view.xml',
        ],
    'demo_xml': [
        ],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
