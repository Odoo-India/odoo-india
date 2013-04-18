
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
    import datetime
    for key,val in mapping.items():
        if key not in fields and values:
            fields.append(key)
            value = values.get(val)
            if key == 'excies_ids':
                if value =='0':
                    excies = conn.get_model("account.tax").search([('name','=','No Excise')])
                    value = [(6,0,excies)]
                elif value == '1':
                    excies = conn.get_model("account.tax").search([('name','=','Excise Duty paid')])
                    value = [(6,0,excies)]
                elif value == '2':
                    excies = conn.get_model("account.tax").search([('name','like','Excise 12%')])
                    value = [(6,0,excies)]
                elif value == '3':
                    excies = conn.get_model("account.tax").search([('name','=','Exise Rate per unit')])
                    value = [(6, 0, excies)]

            if key == 'payment_term_id':
                value = '30 Net Days'

            if key == 'insurance_type':
                value = 'fix'
                
            if key == 'insurance':
                value = '0.0'
            
            if key =='date_order':
                if value == 'NULL' or value == '' or value == '00:00.0' or value == '  ':
                    value = ''
                else:
                    value=datetime.datetime.strptime(value, '%d-%m-%y').strftime("%Y-%m-%d")
            print "value", value
            data_lst.append(value)
    fields.append('location_id')
    data_lst.append('000')
    fields.append('pricelist_id')
    data_lst.append('Default Purchase Pricelist')

    return fields, data_lst

class Parser(object):
    connection = None

    def __init__(self, connection):
        self.connection = connection

    def import_postcode(self, lines):
        connection = self.connection
        postal_pool = connection.get_model("purchase.order")
#        fiscalyear_pool = connection.get_model("account.fiscalyear")
        mapping = {
            "po_series_id": "POSERIES",
            "name": "PONO",
            "date_order": "PODATE",
            "partner_id": "SUPPCODE",
            #"notes": "YOURREF",
           # "excies_ids":"EXCISE",
           # "vat_ids":"SALETAX",
            "delivey":"MILDELIV",
           # "freight":"FREIGHT",
            "payment_term_id":"PAYTERM",
            #"ADVAMOUNT":"ADVAMOUNT"
            "insurance_type":"INSURANCE",
            "insurance":"INSAMOUNT",
            #"DESPATCH":"DESPATCH"
            "notes":"REMARK1",
            "notes4":"REMARK4",
            #"CHGPODATE":"CHGPODATE"
            #"EXITEMS":"EXITEMS",
        }
        values = []
        i = 1
        for line in lines:
            fields, value =  get_field_mapping(connection, line, mapping)
            values.append(value)
        (p, r, warning, s) = postal_pool.import_data(fields, values, mode='init')
        print "POHEADER import successfully",p, r, warning, s

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
        data_lines = read_csv_data(root_path + "POHEADER.csv")
        parser = Parser(connection)
        parser.import_postcode(data_lines)
    except Exception, e:
        print e

if __name__ == '__main__':
    main()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
