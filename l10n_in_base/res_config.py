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

import logging

from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)

class indian_base_configuration(osv.osv_memory):
    _name = 'indian.base.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'module_stock_indent': fields.boolean('Use indent management',
            help = """Allows you to keeps track of internal material request.
            It installs the stock_indent module."""),
        'module_stock_gatepass': fields.boolean('Use gatepass system',
            help = """Allows gate keeper to pass the outgoing materials, products, etc. and keeps track of returning items.
            It installs the stock_gatepass module."""),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
