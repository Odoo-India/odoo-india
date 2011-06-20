
total = 0
class stock():

    def insertGodowns(self, cr, uid, godownObj, dic, com):
        USAGE = 'view'
        godown_id = 0
        if dic.has_key('NAME') and dic['NAME']:
            NAME = dic['NAME']
        if dic.has_key('PARENT') and dic['PARENT']:
            USAGE = 'internal'
            PARENT = dic['PARENT']
            domain = [('name','=',PARENT),('company_id','=',com.id)]
            parent_id = godownObj.search(cr, uid, domain)
            data = {'name':NAME, 'usage':USAGE, 'location_id':parent_id[0], 'company_id':com.id}
            godown_id = godownObj.search(cr, uid, [('name','=',NAME),('company_id','=',com.id)])
        else:
            godown_id = godownObj.search(cr, uid, [('name','=',NAME)])
            data = {'name':NAME, 'usage':USAGE, 'company_id':com.id}
            
        if godown_id:
            godownObj.write(cr, uid, godown_id[0], data)
        else:
            godown_id = godownObj.create(cr, uid, data)

        return True

    def insertCurrencies(self, cr, uid, currencyObj, dic, com):
        rounding = 1.0
        if dic.has_key('NAME') and dic['NAME']:
            SYMBOL = dic['NAME']
        if dic.has_key('EXPANDEDSYMBOL') and dic['EXPANDEDSYMBOL']:
            NAME = dic['EXPANDEDSYMBOL']
        if dic.has_key('DECIMALPLACES') and dic['DECIMALPLACES'] != '0':
            ROUNDING =  1 / ( pow(10,float(dic['DECIMALPLACES'])) )

        data = {'name':NAME, 'symbol':SYMBOL, 'rounding':ROUNDING, 'company_id':com.id}
        currency_id = currencyObj.search(cr, uid, [('name','=',NAME),('company_id','=',com.id)])
        if currency_id:
            currencyObj.write(cr, uid, currency_id[0], data)
        else:
            currencyObj.create(cr, uid, data)
        return True
    
      
    
    def insertUnits(self, cr, uid, uomObj, dic):
        if dic.has_key('ISSIMPLEUNIT') and dic['ISSIMPLEUNIT'] == 'No':
            return {}
        
        rounding = 1.0
        if dic.has_key('DECIMALPLACES') and dic['DECIMALPLACES'] != '0':
            rounding =  1 / ( pow(10,float(dic['DECIMALPLACES'])) )

        data = {'name':dic['VOUCHERTYPENAME'], 'category_id':1 , 'factor':1.0 , 'rounding':rounding, 'uom_type':'reference'}
        
        sid = uomObj.search(cr, uid, [('name','=',dic['VOUCHERTYPENAME'])])
        if sid:
            uomObj.write(cr, uid, sid[0], data)
        else:
            return uomObj.create(cr, uid, data)
    
    def insertStockGroups(self, cr, uid, prodCatObj, dic):
        if dic.has_key('PARENT') and dic['PARENT']:
            pid = prodCatObj.search(cr, uid, [('name','=',dic['PARENT'])])
        else:
            pid = prodCatObj.search(cr, uid, [('name','=','All products')])
        
        data = {'name': dic['VOUCHERTYPENAME'], 'parent_id':pid[0], 'type':'normal'}
        
        sid = prodCatObj.search(cr, uid, [('name','=',dic['VOUCHERTYPENAME'])])
        if sid:
            prodCatObj.write(cr, uid, sid[0], data)
        else:    
            return prodCatObj.create(cr, uid, data)
            
 
    def insertStockItems(self, cr, uid, prodObj, uomObj, prodCatObj, dic, com):
        global total
        costing_met = 'standard'
        std_price = 0.0
       
        if dic.has_key('OPENINGVALUE') and dic['OPENINGVALUE']:
            opening_value = dic['OPENINGVALUE']
            if float(opening_value) < 0:
                opening_value = (float(opening_value) * (-1))
            print "Opening Balance H/W & S/W",opening_value,dic['NAME']
            total = total + float(opening_value) 
        print "Total Opening Balance",total
           
        if dic.has_key('OPENINGRATE') and dic['OPENINGRATE']:
            std_price = float(dic['OPENINGRATE'].split('/')[0])
        
        uomID = uomObj.search(cr, uid, [('name','=',dic['BASEUNITS'])])
        if not uomID:
            obj = stock()
            uomID = obj.insertUnits(cr, uid, uomObj, {'VOUCHERTYPENAME':dic['BASEUNITS']})
        else:
            uomID = uomID[0]    
            
        categID = prodCatObj.search(cr, uid, [('name','=',dic['PARENT'])])
        if not categID:
            obj = stock()
            categID = obj.insertStockGroups(cr, uid, prodCatObj, {'VOUCHERTYPENAME':dic['PARENT']})
        else:
            categID = categID[0]
        
        if dic.has_key('COSTINGMETHOD') and dic['COSTINGMETHOD'] == "Avg. Cost":
            costing_met = 'average'
           
        #if company is selected then the product will belong to that company.
        if com:
            data = {'name':dic['VOUCHERTYPENAME'], 'cost_method':costing_met, 'uom_id':uomID, 'uom_po_id':uomID, 'standard_price':std_price, 'categ_id':categID, 'company_id':com.id}
        else:
            data = {'name':dic['VOUCHERTYPENAME'], 'cost_method':costing_met, 'uom_id':uomID, 'uom_po_id':uomID, 'standard_price':std_price, 'categ_id':categID}
        
        #if record is already exist then it will updated else new record is created.
        sid = prodObj.search(cr, uid, [('name','=',dic['VOUCHERTYPENAME']),('company_id','=',com.id)])
        if sid:
            prodObj.write(cr, uid, sid[0], data)
        else:    
            return prodObj.create(cr, uid, data)
        
        
        
        
        
