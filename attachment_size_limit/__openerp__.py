# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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
    'name': 'Attachment Size Limit',
    'category': 'Hidden',
    'version' : '1.1',
    'author' : 'OpenERP S.A.',
    'sequence': 120,
    'summary': 'Limits on # file, size on uploads, Block users for uploading',
    'description': """
Attachment Configuration
========================

* **Company Configuration you can control this three things.**

  * Maximum files allowed to upload per record.
  * Maximum size of file that can be uploaded.
  * Block User.
""",
    'depends': ['web','base','document'],
    'js': [
        'static/src/js/attachment_size_limit.js',
    ],
    'data': [
        'res_company_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
