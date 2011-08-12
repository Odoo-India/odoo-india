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

import string

class employee():

    def insertEmployees(self, cr, uid, empObj, dic, com):

        if dic.has_key('GENDER') and dic['GENDER']:
            gen = string.lower(dic['GENDER'])
            if gen[0] == 'm':
                gender = 'male'
            elif gen[0] == 'f':
                gender = 'female'
            else:
                return True
        else:
            return True

        name = ''
        mobile = ''
        email = ''
        location = ''

        if dic.has_key('NAME') and dic['NAME']:
            name = dic['NAME']
         
        if dic.has_key('CONTACTNUMBERS') and dic['CONTACTNUMBERS']:
            mobile = dic['CONTACTNUMBERS']
         
        if dic.has_key('EMAILID') and dic['EMAILID']:
            email = dic['EMAILID']
         
        if dic.has_key('LOCATION') and dic['LOCATION']:
            location = dic['LOCATION']

        data = {'name':name, 'company_id':com.id, 'gender':gender, 'mobile_phone':mobile, 'work_email':email, 'work_location':location}

        if dic.has_key('DATEOFBIRTH') and dic['DATEOFBIRTH']:
            data['birthday'] = dic['DATEOFBIRTH']
         

        domain = [('name','=',name),('company_id','=',com.id)]
        emp_id = empObj.search(cr, uid, domain)
        if emp_id:
            empObj.write(cr, uid, emp_id, data)
        else:
            emp_id = empObj.create(cr, uid, data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
