
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com
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
###############################################################################


{
    'name': 'HR Payroll with TDS linking',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
This module can line TDS payable  lines to TDS entries, hence letting to get all TDS related reports.

     """,
    'author': 'Selvam(selvam@e-ndicus.com)',
    'website': 'http://e-ndicus.com',
    'depends': ['base','account','hr_payroll','hr_payroll_account','account_india_tds'],
    'init_xml': [
],
    'update_xml': ['hr_payroll_tds_view.xml'],
    'demo_xml': [
],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
