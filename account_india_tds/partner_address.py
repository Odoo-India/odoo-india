
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

#disabled now
from osv import osv, fields
import time
import datetime
class part_addr(osv.osv):
    """Adding flat and building name which are needed for Form 26q"""
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _columns = {
     'flat_no':fields.char('Flat No',size=128),
     'build_name':fields.char('Building Name',size=256),
    }
part_addr()
