
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

def get_field_mapping(values, mapping):
    """
    Final Field Mapper for the Preparing Data for the Import Data
    """
    fields=[]
    data_lst = []
    for key,val in mapping.items():
        if key not in fields and values:
            fields.append(key)
            value = values.get(val)
            if value == ' ' and key=='raw_code_id':
                value=''
            if value == '  ' and key=='series_id':
                value=''
            if value == ' ' and key=='state_id':
                value=''
            if value == ' ' and key=='md_code':
                value=''
            if key=='stno_1':
                if value == 'Y' and key=='c_form':
                    value = '1'
                if value == ' ' and key=='c_form':
                    value = '0'
            if key == 'bank_code_id':
                if value == ' ':
                    value = ''
                else:            
                    value == value
            if key == 'state_id':
                if value == 'KARNATAK':
                    value = 'KARNATAKA'
                if value == 'DELHI                         ' or value == 'NEW DELHI':
                    value = 'DELHI'
                if value == 'UTTAR PRADESH                 ':
                    value = 'UTTAR PRADESH'
                if value == 'PONDICHERY':
                    value = 'PONDICHERRY'
                if value == 'CHHATISHGARDH':
                    value = 'CHANDIGARH'
                if value == 'MAHARASHTRA':
                    value = 'MAHARASTRA'
                if value == 'TAMIL NADU' or value =='TAMILNADU                     ':
                    value = 'TAMILNADU'
                if value == 'GUJRAT' or value == 'GUJAAT' or value == 'AHMEDABAD' or value == 'GUJARTAT':
                    value = 'GUJARAT'
                if value == 'PUNJAB                        ':
                    value = 'PUNJAB'
                if value == 'WEST BENGAL                   ':
                    value = 'WEST BENGAL'
                if value == 'UNITED STATE OF AMERICA' or value == 'U.S.A.':
                    value = 'USA'
                if value == 'CIPUZKOA':
                    value = ''
                if value == 'TURKIYE' or value=='TURKEY':
                    value = ''
                if value == 'CHINA':
                    value = ''
                if value == '0265-2226004':
                    value = ''
                if value == 'AUSTRIA':
                    value = ''
                if value == 'ELIZABETH WEST':
                    value = ''
                if value == 'GERMANY':
                    value = ''
            data_lst.append(value)
    fields.append('supplier')
    data_lst.append('1')
    fields.append('is_company')
    data_lst.append('1')
    return fields, data_lst

class Parser(object):
    connection = None

    def __init__(self, connection):
        self.connection = connection

    def import_postcode(self, lines):
        connection = self.connection
        postal_pool = connection.get_model("res.partner")
#        fiscalyear_pool = connection.get_model("account.fiscalyear")

        mapping = {
            "supp_code":"SUPPCODE",
            "name":"SUP_NAME",
            "comment":"SUP_DESCR",
            "street":"ADDR1",
            "street2":"ADDR2",
            "street3":"ADDR3",
            "city":"CITY",
            "zip":"PIN",
            "state_id":"STATE",
#            "tax_code_id":"TAXCODE",
            "raw_code_id":"RAWCODE",
            "bank_code_id":"BANKCODE",
            "md_code":"MDCODE",
            "phone":"PHONE",
            "mobile":"MOBILE",
            "series_id":"SERIES",
            "tds_per":"TDSPER",
            "c_form":"CFORMIND",
            "fax":"FAX",
            "pan_no":"PANNO",
            "email":"MAILID",
            "stno_1":"STNO_1",
            "stno_2":"STNO_2",
            "ecc_code":"ECCCODE",
            "ser_tax_reg_no":"SERTAXREGNO",
            "cst_no":"CSTNO",
        }
        values = []
        i = 1
        count = 0
        for line in lines:
            fields, value =  get_field_mapping(line, mapping)
            values.append(value)
            count+=1
        (p, r, warning, s) = postal_pool.import_data(fields, values, mode='init')
        print "Import supplier sucessfully", p, r, warning, s


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

        data_lines = read_csv_data(root_path + "SUPLMST.csv")
        parser = Parser(connection)
        parser.import_postcode(data_lines)
    except Exception, e:
        print e

if __name__ == '__main__':
    main()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
