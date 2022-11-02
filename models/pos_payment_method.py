# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from lxml.builder import ElementMaker
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
import base64
import logging
import xmltodict, json
import random
import uuid
import time
from urllib.request import urlopen
from odoo import http
from odoo.http import request
import time
_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
          return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('netpay', 'netpay')]

    netpay_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    netpay_latest_response = fields.Char(help='Technical field used to buffer the latest asynchronous notification from Adyen.', copy=False, groups='base.group_erp_manager')
    netpay_latest_diagnosis = fields.Char(help='Technical field used to determine if the terminal is still connected.', copy=False, groups='base.group_erp_manager')
    netpay_terminal_identifier = fields.Char(help='[Terminal model]-[Serial number], for example: P400Plus-123456789', copy=False)
   #credentials
    terminal_api_key = fields.Char('API Key')
    terminal_api_pwd = fields.Char('API Password')
    terminal_id = fields.Char('Terminal ID')


    def proxy_netpay_request(self, data, operation):
        logging.warning('proxy_netpay_request')

        return self._proxy_netpay_request_direct(data, operation)

    def _get_netpay_endpoints(self, operation):
        url = "http://nubeqa.netpay.com.mx:3334/integration-service/transactions/sale"
        if operation == 'sale':
            url = "http://nubeqa.netpay.com.mx:3334/integration-service/transactions/sale"
        if operation == 'cancel':
            url = "http://nubeqa.netpay.com.mx:3334/integration-service/transactions/cancel"
        if operation == 'reprint':
            url = "http://nubeqa.netpay.com.mx:3334/integration-service/transactions/reprint"

        return url

    def get_latest_netpay_status(self, pos_config_name, order_uid):
        logging.warning('Función get_latest_adyen_status')
        _logger.info('get_latest_adyen_status\n%s', pos_config_name)
        self.ensure_one()

        latest_response = self.sudo().netpay_latest_response

        logging.warning('latest_response, cruzar dedos')
        logging.warning(latest_response)
        latest_response = json.loads(latest_response) if latest_response else False

#         logging.warning(latest_response[0])
        logging.warning('')
        if latest_response != False:
            if "folioNumber" in latest_response:

#             latest_response_dumps=json.dumps(latest_response)
                if order_uid == latest_response['folioNumber']:
                    logging.warning('Si son iguales')


                else:
                    logging.warning('No es Igual llllllllllll')
                    latest_response = False
        logging.warning('Antes del return :::C')
        logging.warning(latest_response)
        return {
            'latest_response': latest_response,
        }

#     def proxy_netpay_request(self, data, operation=False):
#         ''' Necessary because Adyen's endpoints don't have CORS enabled '''
#         if data['orderId'] == 'Payment': # Clear only if it is a payment request
#             self.sudo().netpay_latest_response = ''  # avoid handling old responses multiple times

#         if not operation:
#             operation = 'terminal_request'

#         return self._proxy_netpay_request_direct(data, operation)

    def _is_write_forbidden(self, fields):
        whitelisted_fields = set(('netpay_latest_response', 'netpay_latest_diagnosis'))
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - whitelisted_fields)

    def _proxy_netpay_request_direct(self, data, operation):
        logging.warning('Function _proxy_netpay_request_direct')
        logging.warning(self)
        for x in self:
            x.ensure_one()
        TIMEOUT = 10
        logging.warning('_proxy_netpay_request_direct')
        logging.warning('request to adyen\n%s' + str(data))

        #environment = 'test' if self.adyen_test_mode else 'live'

        refresh_token_config = False
        if operation == 'sale':
            endpoint = self._get_netpay_endpoints(operation)
            if 'traceability' in data and data['traceability'] and 'access_token' in data['traceability'] and data['traceability']['access_token']:
                refresh_token_config = data['traceability']['access_token']
            headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer '+str(refresh_token_config)
            }
            traceability_dic = {}
            serial_number = False
            if 'serialNumber' in data:
                serial_number=data['serialNumber']
            store_id = False
            if 'storeId' in data:
                store_id = data['storeId']
            amount=False
            if 'amount' in data:
                amount = data['amount']
            folio_number = False
            if 'folioNumber' in data:
                folio_number = data['folioNumber']

            serial_number = False
            if "traceability" in data:
                if "serial_number" in data["traceability"]:
                    serial_number = data["traceability"]["serial_number"]

            json_data = {
                'serialNumber': serial_number,
                'amount': amount,
                'storeId': store_id,
                'folioNumber': folio_number,
                'msi': "",
                "traceability": {
                    'type':'sale',
                    'serial_number':serial_number
                }
            }
            logging.warning('endpoint--')
            logging.warning(endpoint)
            logging.warning(json_data)
            logging.warning('...........')
            logging.warning('')
            logging.warning('')
            req = requests.post(endpoint, data = json.dumps(json_data), headers = headers)
            logging.warning('Request---------1')
            logging.warning(req)
            logging.warning(req.content)
            #req = requests.post(endpoint, json=data, headers=headers, timeout=TIMEOUT)


            if req.status_code == 200:
                if req.content:
                    response_content = req.content.decode('utf8')
                    response_json = json.loads(response_content)
                    # if 'access_token' in response_json:
                    #     self.access_token = response_json['access_token']
                    # if 'refresh_token' in response_json:
                    #     self.refresh_token = response_json['refresh_token']
                    logging.warning('status code')
                    logging.warning(req.status_code)
                    return True


            if req.status_code != 200:
                response_content = req.content.decode('utf8')
                logging.warning('error')
                logging.warning(response_content)
                logging.warning(response_content[0])
                json_loads = json.loads(response_content)
                logging.warning(json_loads["error_description"])
                if "error_description" in json_loads:
                    logging.warning('Entro al IF?')
                    return {
                        'error':{
                            'status_code': req.status_code,
                            'message': json_loads["error_description"],

                        }
                    }
                        #output['error'] = response_content

            # Authentication error doesn't return JSON
            #if req.status_code == 401:
             #   return {
              #      'error': {
               #         'status_code': req.status_code,
                #        'message': req.text
                 #   }
                #}

            #if req.text == 'ok':
             #   return True

            return req.json()

        if operation == 'cancel':
            endpoint = self._get_netpay_endpoints(operation)
            logging.warning('Bienvenido a una función con opcion cancel')
            if ("traceability" and "serialNumber" and "orderId" and "storeId") in data:
                refresh_token_config = False

            if 'traceability' in data and data['traceability'] and 'refresh_token' in data['traceability'] and data['traceability']['refresh_token']:
                refresh_token_config = data['traceability']['refresh_token']
            headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer '+str(refresh_token_config)
            }
            serial_number = False
            if "serialNumber" in data:
                serial_number = data["serialNumber"]
            order_id = False
            if "orderId" in data:
                order_id = data["orderId"]
            if "storeId" in data:
                store_id = data["storeId"]


            json_data = {
                "traceability": {
                    "cancel": True,
                    'type': 'cancel'
                },
                "serialNumber": str(serial_number),
                "orderId": str(order_id),
                "storeId": str(store_id),
            }

            logging.warning('endpoint--')
            logging.warning(endpoint)
            logging.warning(json_data)
            logging.warning('...........')
            logging.warning('')
            logging.warning('')
            req = requests.post(endpoint, data = json.dumps(json_data), headers = headers)
            logging.warning('Request---------2 cancel')
            logging.warning(req)
            logging.warning(req.content)

            if req.status_code == 200:
                if req.content:
                    response_content = req.content.decode('utf8')
                    response_json = json.loads(response_content)
                    logging.warning('status code')
                    logging.warning(req.status_code)
                    return True

            if req.status_code != 200:
                response_content = req.content.decode('utf8')
                logging.warning('error')
                logging.warning(response_content)
                logging.warning(response_content[0])
                json_loads = json.loads(response_content)
                if "error_description" in json_loads:
                    logging.warning('Entro al IF?')
                    logging.warning(json_loads["error_description"])
                    return {
                        'error':{
                            'status_code': req.status_code,
                            'message': json_loads["error_description"],

                        }
                    }

            return req.json()

        if operation == 'reprint':
            endpoint = self._get_netpay_endpoints(operation)
            logging.warning('Bienvenido a una función con opcion reprint')
            if ("traceability" and "serialNumber" and "orderId" and "storeId") in data:
                refresh_token_config = False

            if 'traceability' in data and data['traceability'] and 'refresh_token' in data['traceability'] and data['traceability']['refresh_token']:
                refresh_token_config = data['traceability']['refresh_token']
            headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer '+str(refresh_token_config)
            }
            serial_number = False
            if "serialNumber" in data:
                serial_number = data["serialNumber"]
            order_id = False
            if "orderId" in data:
                order_id = data["orderId"]
            if "storeId" in data:
                store_id = data["storeId"]


            json_data = {
                "traceability": {
                    "reprint": True,
                    "type": 'reprint'
                },
                "serialNumber": str(serial_number),
                "orderId": str(order_id),
                "storeId": str(store_id),
            }

            logging.warning('endpoint--')
            logging.warning(endpoint)
            logging.warning(json_data)
            logging.warning('...........')
            logging.warning('')
            logging.warning('')
            req = requests.post(endpoint, data = json.dumps(json_data), headers = headers)
            logging.warning('Request---------2 reprint')
            logging.warning(req)
            logging.warning(req.content)

            if req.status_code == 200:
                if req.content:
                    response_content = req.content.decode('utf8')
                    response_json = json.loads(response_content)
                    logging.warning('status code')
                    logging.warning(req.status_code)
                    return True

            if req.status_code != 200:
                response_content = req.content.decode('utf8')
                logging.warning('error')
                logging.warning(response_content)
                logging.warning(response_content[0])
                json_loads = json.loads(response_content)
                if "error_description" in json_loads:
                    logging.warning('Entro al IF?')
                    logging.warning(json_loads["error_description"])
                    return {
                        'error':{
                            'status_code': req.status_code,
                            'message': json_loads["error_description"],

                        }
                    }

            return req.json()
