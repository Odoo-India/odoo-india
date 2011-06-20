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
