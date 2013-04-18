
import csv
import os
import optparse
import openerplib
import CONNECTION

def read_csv_data(path):
    """
        Reads CSV from given path and Return list of dict with Mapping
    """
    data = csv.reader(open(path))
    # Read the column names from the first line of the file
    fields = data.next()
    data_lines = []
    for row in data:
        items = dict(zip(fields, row))
        data_lines.append(items)
    return data_lines

def get_field_mapping(conn, values, mapping):
    """
    Final Field Mapper for the Preparing Data for the Import Data
    """
    fields=[]
    data_lst = []
    for key,val in mapping.items():
        if key not in fields and values:
            fields.append(key)
            value = values.get(val)
            if key == 'default_code':
                value='0'+value
            if key == 'status':
                if value ==' ':
                    value = ''
            if key == 'last_po_series':
                if value ==' ':
                    value = ''
            if value == '  ' and key=='item_type':
                value=''
            if key =='last_po_date':
                import datetime
                if value == 'NULL' or value == '':
                    value = ''
                else:
                    value=datetime.datetime.strptime(value, '%d/%m/%Y').strftime("%Y-%m-%d")
            if key == 'last_supplier_code/.id':
                supplier = conn.get_model("res.partner").search([('supp_code','=',value)])
                if supplier == [] or supplier == False:
                    value=''
                else:
                    value=supplier[0]
            data_lst.append(value)
        if key == 'default_code':
            fields.append('categ_id')
            if value[0:2] == "01":
                data_lst.append('Local')
            elif value[0:2] == "02":
                data_lst.append('Imported')

        if key == 'default_code':
            fields.append('major_group_id/.id')
            major = conn.get_model("product.major.group").search([('code','=',value[2:4])])
            data_lst.append(major[0])
        if key == 'default_code':
            sub = conn.get_model("product.sub.group").search([('code','=',value[4:6])])
            fields.append('sub_group_id/.id')
            data_lst.append(sub[0])
    fields.append('purchase_requisition')
    data_lst.append('1')
    return fields, data_lst

class Parser(object):
    connection = None

    def __init__(self, connection):
        self.connection = connection

    def import_postcode(self, lines):
        connection = self.connection
        postal_pool = connection.get_model("product.product")
#        fiscalyear_pool = connection.get_model("account.fiscalyear")
        mapping = {
            "default_code": "ITEMCODE",
            "name": "DESCR1",
            "desc2": "DESCR2",
            "desc3": "DESCR3",
            "desc4": "DESCR4",
            "uom_id":"UNIT",
            "uom_po_id":"UNIT",
            #"type":"Stockble Product",
            #"variance":"VARIANCE",
            "item_type":"ITEMTYPE",
            #"purchase_requisition":"1",
            'location':"LOCATION",
            "ex_chapter":"EXCHAPTER",
            "ex_chapter_desc":"EXCHAPTERDESCR",
            "last_po_date":"LPODATE",
            "last_po_year":"LPOYEAR",
            #"last_po_no":"LPONUMBER",
            "last_supplier_code/.id":"LSUPPCODE",
            "last_supplier_rate":"LSUPPRATE",
            #"cy_opning_qty":"CYROPNQTY",
            #"cy_opning_value":"CYROPNVLU",
            #"cy_issue_qty":"CYRISUQTY",
            #"cy_issue_value":"CYRISUVLU",
            #"last_receive_date":"LRECVDATE",
            #"last_receive_qty":"LYRECPQTY",
            #"last_receive_value":"LYRECPVLU",
            #"last_issue_date":"LISSUDATE",
            #"last_issue_qty":"LYRISUQTY",
            #"last_issue_value":"LYRISUVLU",
            "status":"STATUS",
            "last_po_series":"LPOSERIES",
        }
        values = []
        i = 1
        for line in lines:
            fields, value =  get_field_mapping(connection, line, mapping)
            values.append(value)
        (p, r, warning, s) = postal_pool.import_data(fields, values, mode='init')
        print "Product import successfully",p, r, warning, s

def configure_parser():
    config = CONNECTION.DefaultConfig()
    parser = optparse.OptionParser(usage='usage: %prog [options]', version='%prog v1.1')

    parser.add_option("--host", dest="host",
                      help="Hostname of the OpenERP Server",
                      default=config.OPENERP_HOSTNAME)

    parser.add_option("-d", "--dbname", dest="dbname",
              help="Database name (default: %default)",
              default=config.OPENERP_DEFAULT_DATABASE)

    parser.add_option("-u", "--user", dest="userid",
              help="ID of the user in OpenERP",
              default=config.OPENERP_DEFAULT_USER_NAME)

    parser.add_option("--defaultpath", "--defaultpath",
              help="Default Import path",
              default=config.DEFAULT_PATH)

    parser.add_option("-p", "--password", dest="password",
              help="Password of the user in OpenERP",
              default=config.OPENERP_DEFAULT_PASSWORD)

    parser.add_option("--port", dest="port",
                  help="Port of the OpenERP Server",
                  default=config.OPENERP_PORT)

    parser.add_option("--path", dest="path",
                      help="Path of import file.",
                      default=os.environ.get('HOME'))
    return parser


def main():
    parser = configure_parser()
    (options, args) = parser.parse_args()
    root_path = options.defaultpath
    try:
        connection = openerplib.get_connection(hostname=options.host,
                                               database=options.dbname,
                                               login=options.userid,
                                               password=options.password,
                                               )
        data_lines = read_csv_data(root_path + "ITEMMAST_all.csv")
        parser = Parser(connection)
        parser.import_postcode(data_lines)
    except Exception, e:
        print e

if __name__ == '__main__':
    main()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
