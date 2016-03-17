# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import logging
import os
import suds  # should work with suds or its fork suds-jurko
import sys

import datetime
from suds.client import Client
from urllib2 import URLError

from pprint import pprint
handler = logging.StreamHandler(sys.stderr)
logger = logging.getLogger('suds.transport.http')
logger.setLevel(logging.DEBUG), handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class AramexRequest():
    """ Low-level object intended to interface Odoo recordsets with Aramex,
        through appropriate SOAP requests """

    def __init__(self, request_type="shipping", test_mode=True):
        if request_type == "shipping":
            wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/shipping-services-api-wsdl.wsdl')
            self.start_shipping_transaction(wsdl_path)
 
        elif request_type == "rating":
            wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/aramex-rates-calculator-wsdl.wsdl')
            self.start_rating_transaction(wsdl_path)

    def client_info(self, user_name, password, version, account_number, account_pin, account_entity, account_country_code):
        self.ClientInfo = self.client.factory.create('ClientInfo')
        self.ClientInfo.UserName = user_name
        self.ClientInfo.Password = password
        self.ClientInfo.Version = version
        self.ClientInfo.AccountNumber = account_number
        self.ClientInfo.AccountPin = account_pin
        self.ClientInfo.AccountEntity = account_entity
        self.ClientInfo.AccountCountryCode = account_country_code

    def transaction_detail(self, reference1):
        self.Transaction = self.client.factory.create('Transaction')
        self.Transaction.Reference1 = reference1

    # Common stuff
    def set_shipper(self, company_partner, warehouse_partner, aramex_account_number=None, mode='rating'):
        self.OriginAddress = self.client.factory.create('Address')
        self.OriginAddress.Line1 = warehouse_partner.street or ''
        self.OriginAddress.Line2 = warehouse_partner.street2 or ''
        self.OriginAddress.City = warehouse_partner.city or ''
        self.OriginAddress.StateOrProvinceCode = warehouse_partner.state_id.code or ''
        self.OriginAddress.PostCode = warehouse_partner.zip or ''
        self.OriginAddress.CountryCode = warehouse_partner.country_id.code or ''
        if mode == 'shipping':
            self.Shipper = self.client.factory.create('Party')
            self.Shipper.AccountNumber = aramex_account_number
            self.Shipper.PartyAddress = self.OriginAddress
            Contact = self.client.factory.create('Contact')
            Contact.PersonName = company_partner.name or ''
            Contact.CompanyName = company_partner.name or ''
            Contact.PhoneNumber1 = company_partner.phone or ''
            Contact.PhoneNumber1Ext = '133'
            Contact.CellPhone = company_partner.mobile or ''
            Contact.EmailAddress = company_partner.email or ''
            self.Shipper.Contact = Contact

    def set_recipient(self, recipient_partner, mode='rating'):
        self.DestinationAddress = self.client.factory.create('Address')
        self.DestinationAddress.Line1 = recipient_partner.street or ''
        self.DestinationAddress.Line2 = recipient_partner.street2 or ''
        self.DestinationAddress.City = recipient_partner.city or ''
        self.DestinationAddress.StateOrProvinceCode = recipient_partner.state_id.code or ''
        self.DestinationAddress.PostCode = recipient_partner.zip or ''
        self.DestinationAddress.CountryCode = recipient_partner.country_id.code or ''
        if mode == 'shipping':
            self.Consignee = self.client.factory.create('Party')
            self.Consignee.PartyAddress = self.DestinationAddress
            Contact = self.client.factory.create('Contact')
            Contact.PersonName = recipient_partner.name or ''
            Contact.CompanyName = recipient_partner.name or ''
            Contact.PhoneNumber1 = recipient_partner.phone or ''
            Contact.PhoneNumber1Ext = ''
            Contact.CellPhone = recipient_partner.mobile or ''
            Contact.EmailAddress = recipient_partner.email or ''
            self.Consignee.Contact = Contact

    def add_package(self, carrier, weight, number_of_pieces=False):
        self.ShipmentDetails = self.client.factory.create('ShipmentDetails')
        self.ShipmentDetails.PaymentType = 'P'
        self.ShipmentDetails.ProductGroup = 'EXP'
        self.ShipmentDetails.ProductType = 'PPX'
        dimensions = self.client.factory.create('Dimensions')
        dimensions.Length = carrier.aramex_package_length
        dimensions.Width = carrier.aramex_package_width
        dimensions.Height = carrier.aramex_package_height
        dimensions.Unit = carrier.aramex_package_dimension_unit
        self.ShipmentDetails.Dimensions = dimensions
        package_weight = self.client.factory.create('Weight')
        package_weight.Unit = carrier.aramex_weight_unit
        package_weight.Value = weight
        self.ShipmentDetails.ActualWeight = package_weight
        self.ShipmentDetails.ChargeableWeight = package_weight
        self.ShipmentDetails.NumberOfPieces = number_of_pieces or 1

    def start_rating_transaction(self, wsdl_path):
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'))

    def rate(self):
        formatted_response = {'price': 0.0, 'currency': False}
        try:
            self.response = self.client.service.CalculateRate(ClientInfo=self.ClientInfo,
                                                         Transaction=self.Transaction,
                                                         OriginAddress=self.OriginAddress,
                                                         DestinationAddress=self.DestinationAddress,
                                                         ShipmentDetails=self.ShipmentDetails)
            if (not self.response.HasErrors):
                formatted_response['price'] = self.response.TotalAmount.Value
                formatted_response['currency'] = self.response.TotalAmount.CurrencyCode
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications.Notification ])
                formatted_response['errors_message'] = errors_message
        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except URLError:
            formatted_response['errors_message'] = "Amrmex Server Not Found"
        return formatted_response

    def start_shipping_transaction(self, wsdl_path):
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'))
        print self.client

    def label_info(self):
        self.LabelInfo = self.client.factory.create('LabelInfo')
        self.LabelInfo.ReportID = '9201'
        self.LabelInfo.ReportType = 'RPT'

    def send_shipping(self):
        self.Shipments = self.client.factory.create('ArrayOfShipment')
        Shipment = self.client.factory.create('Shipment')
        Shipment.Shipper = self.Shipper
        Shipment.Consignee = self.Consignee
        Shipment.ShippingDateTime = datetime.datetime.today()
        Shipment.DueDate = datetime.datetime.today()
        Shipment.Details = self.ShipmentDetails
        self.Shipments.Shipment = Shipment

    def print_label(self):
        return self.client.service.PrintLabel(ClientInfo=self.ClientInfo,Transaction=self.Transaction,ShipmentNumber='3957830531',LabelInfo=self.LabelInfo)
        
    def send_shipment(self):
        formatted_response = {'form_id': 0, 'tracking_number': 0.0, 'label': False}
        try:
            self.response = self.client.service.CreateShipments(ClientInfo=self.ClientInfo,
                                                             Shipments=self.Shipments,
                                                             LabelInfo=self.LabelInfo
                                                             )
            if (not self.response.HasErrors):
                formatted_response['tracking_number'] = self.response.Shipments.ProcessedShipment[0].ID
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications.Notification ])
                formatted_response['errors_message'] = errors_message
        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except URLError:
            formatted_response['errors_message'] = "Aramex Server Not Found"

        return formatted_response

    def get_label(self):
        return self.response.Shipments.ProcessedShipment[0].ShipmentLabel.LabelFileContents

#-----------------------------------------------
#ShipmentCreationRequest
#aramex = AramexRequest()
#aramex.client_info('testingapi@aramex.com', 'R123456789$r', '1.0', '20016', '331421', 'AMM', 'JO')
#aramex.transaction_detail('001')
#aramex.label_info()
#aramex.create_shipment()
#import pdb
#pdb.set_trace()
#print aramex.process_shipment()

#-----------------------------------------------
#LabelInfo
#aramex = AramexRequest()
#aramex.client_info('testingapi@aramex.com', 'R123456789$r', '1.0', '20016', '331421', 'AMM', 'JO')
#aramex.transaction_detail('001')
##aramex.create_shipment('20016')
#aramex.label_info()
#print aramex.print_label()

#-----------------------------------------------
#Rating Request
#aramex = AramexRequest(request_type="rating")
#aramex.client_info('testingapi@aramex.com', 'R123456789$r', '1.0', '20016', '331421', 'AMM', 'JO')
#aramex.transaction_detail('001')
#aramex.set_shipper('Mecca St', '', 'Amman', '', '', 'Jo')
#aramex.set_recipient('15 ABC St', '', 'Dubai', '', '', 'AE')
#aramex.add_package(5, 'KG', 5)
#print "------>>",aramex.rate()
