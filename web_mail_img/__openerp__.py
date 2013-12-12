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
    'name': 'Zoom Image',
    'category': 'Tools',
    'description': """
Zoom Images In Mail Attachment
==============================
    """,
    "author": "OpenERP SA",
    "website": "http://www.openerp.com",
    'depends': ["base","mail"],
    'init_xml': [],
    'data': [
             ],
        'css':[
        'static/src/css/web_mail_img.css',
    ],
    "js" : [
        "static/src/js/zoomit.jquery.js",
        "static/src/js/web_mail_img.js",
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
