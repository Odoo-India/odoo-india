
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com,Karl-karl@e-ndicus.com
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
    "name" : "Account TDS Report",
    "version" : "1.0",
    "depends" : ["base","account","account_base"],
    "author" : "Karl Marx",
    "description": """ TDS report create
    """,
    'website': 'http://e-ndicus.com',
    'init_xml': [],
    'update_xml': [       
        'wizard/tds_report_form16a.xml',

	'tds_report.view.xml'
	
    ],
    
    'installable': True,
    'active': False,
}
