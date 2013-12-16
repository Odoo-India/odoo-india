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

from openerp.osv import fields, osv

class res_company(osv.Model):
    _name = "res.company"
    _inherit = "res.company"
    
    _columns = {
       'attachment_size': fields.integer("Maximum Size", help="Maximum size of attachment allowed to upload, i.e 5 represent by 5MB"),
       'attachment_num': fields.integer("# of Attachments", help="Maximum attachment allowed to attach per record"),
       'user_blocked': fields.many2many('res.users', 'attachment_user_rel', 'user_id', 'attach_id', 'Blocked Users', help="user listed here will not be able to attach files on any record"),
    }
    
    _defaults = {
        'attachment_size':10240,
        'attachment_num':5
    }
res_company()