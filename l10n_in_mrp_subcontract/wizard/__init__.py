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

import process_qty_to_reject
import process_qty_to_finished
import all_in_once_qty_to_finished
import all_in_once_qty_to_cancelled
import reallocate_rejected_move
import generate_service_order
import qty_to_consume
import add_rawmaterial_to_consume
import consignment_variation_po
import qc2xlocation
import stock_return_picking
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: