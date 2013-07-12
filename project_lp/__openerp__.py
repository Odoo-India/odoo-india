# -*- encoding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2004-2011 OpenERP s.a. (<http://www.openerp.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Launchpad Integration',
    'version': '1.0',
    'category': 'Generic Modules/Project Management',
    'description': """
Integration with Launchpad
======================================================================================
Provides integration between OpenERP and Launchpad.
    """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': ["project"],
    'init_xml': [],
    'update_xml': [
        "project_launchpad_view.xml",
        "project_scheduler.xml",
        "wizard/project_launchpad.xml",
        "report/report_project_branch_merge_view.xml"
    ],
    'test':[],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
