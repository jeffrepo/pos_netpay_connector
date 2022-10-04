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

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def sale_netpay_ui(self, order):
        output = {'error': False, 'transaction': False}
        sesiones = self.env['pos.session'].search([('id', '=', order[0]['data']['pos_session_id'])])
        if sesiones:
            refresh_token_config = False
            serial_number = False
            store_id = sesiones.config_id.store_id_netpay
            for sesion in sesiones:
                if sesion.config_id.refresh_token == False:
                    return super(PosOrder, self)._process_order(order, draft, existing_order)
                else:
                    refresh_token_config = sesion.config_id.access_token
                    serial_number = sesion.config_id.serial_number

            logging.warning('refresh_token')
            logging.warning(refresh_token_config)

            if refresh_token_config:

                logging.warning('test pos')

                payload = ""

                url = "http://nubeqa.netpay.com.mx:3334/integration-service/transactions/sale"
                headers = {
                  'Content-Type': 'application/json',
                  'Authorization': 'Bearer '+str(refresh_token_config)
                }
                traceability_dic = {

                }

                json_data = False
                logging.warning(order)
                if len(order) > 0:
                    if 'data' in order[0]:
                        if 'lines' in order[0]['data']:
                            json_data = {
                                'serialNumber': serial_number,
                                'amount': 0.00,
                                'storeId': store_id,
                                'folioNumber': False,
                                'msi': "03",
                                "traceability": {
                                        "idProducto": '',
                                        "idTienda": store_id
                                }
                            }



                            json_data['amount'] = order[0]['data']['amount_total']
                            json_data['folioNumber'] = order[0]['id']
                            json_data['traceability']['idProducto'] = order[0]['id']

                            # for linea in order[0]['data']['lines']:
                            #     logging.warning('la linea')
                            #     logging.warning(linea)
                            #     traceability_dic

                # traceability_dic = {
                #
                # }
                #
                if json_data:

                    # # auth=HTTPBasicAuth('trusted-app', 'secret')
                    response = requests.post(url, data = json_data, headers = headers)
                    # logging.warning(response)
                    # logging.warning(response.content)
                    logging.warning(response)
                    logging.warning(response.content)
                    if response.status_code == 200:
                        if response.content:
                            response_content = response.content.decode('utf8')
                            response_json = json.loads(response_content)
                            # if 'access_token' in response_json:
                            #     self.access_token = response_json['access_token']
                            # if 'refresh_token' in response_json:
                            #     self.refresh_token = response_json['refresh_token']
                            logging.warning('status code')
                            logging.warning(response.status_code)
                    else:
                        if response.content:
                            response_content = response.content.decode('utf8')
                            logging.warning('error')
                            logging.warning(response_content)
                            if 'message' in response_content:
                                output['error'] = response_content
                                # raise UserError(response_content)
                else:
                    output['error'] = 'Error odoo netpay'

        return output

    def netpay_connection(self, extra_info):
        logging.warning('test')

        payload = ""

        url = "http://nubeqa.netpay.com.mx:3334/oauth-service/oauth/token"
        if 'new_token' in extra_info:
            payload = 'grant_type=password&username=Nacional&password=netpay'
        if 'refresh_token' in extra_info:
            payload = 'grant_type=refresh_token&refresh_token='+str(extra_info['refresh_token'])
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Basic dHJ1c3RlZC1hcHA6c2VjcmV0'
        }
        # auth=HTTPBasicAuth('trusted-app', 'secret')
        response = requests.post(url, data = payload, headers = headers)
        logging.warning(response)
        logging.warning(response.content)
        if response.status_code == 200:
            if response.content:
                response_content = response.content.decode('utf8')
                response_json = json.loads(response_content)
                if 'access_token' in response_json:
                    self.access_token = response_json['access_token']
                if 'refresh_token' in response_json:
                    self.refresh_token = response_json['refresh_token']
                logging.warning('status code')
                logging.warning(response.status_code)
        else:
            if response.content:
                response_content = response.content.decode('utf8')
                logging.warning(response_content)
                if 'error_description' in response_content:
                    raise UserError(response_content)
        return True

    def get_first_token(self):
        self.netpay_connection({'new_token'})

        return True

    def get_refresh_token(self):
        self.netpay_connection({'refresh_token': self.refresh_token})

        return True


    def value_fields(self, dicc):
        logging.warning('Funcion value_fields')
        logging.warning(dicc)

        orders = self.env['pos.order'].search([('id', '=', dicc[0]['id_order'])])
        for order in orders:
            if dicc[0]['TransactionId']:
                order.transaccion_id = dicc[0]['TransactionId']
            if dicc[0]['TransactionDate']:
                order.transaccion_date = dicc[0]['TransactionId']
            if dicc[0]['ProviderAuthorization']:
                order.provider_authorizacion = dicc[0]['ProviderAuthorization']
            if dicc[0]['AditionalInfo1']:
                order.add_info1 = dicc[0]['AditionalInfo1']
            if dicc[0]['AditionalInfo2']:
                order.add_info2 = dicc[0]['AditionalInfo2']
            if dicc[0]['AditionalInfo4']:
                order.add_info3 = dicc[0]['AditionalInfo4']
            if dicc[0]['LegalInformation']:
                order.legal_info = dicc[0]['LegalInformation']
            if 'reference1' in dicc and dicc[0]['reference1']:
                order.reference_1 = dicc[0]['reference1']
            if 'reference2' in dicc and dicc[0]['reference2']:
                order.reference_2 = dicc[0]['reference2']
            if 'reference3' in dicc and dicc[0]['reference3']:
                order.reference_3 = dicc[0]['reference3']

        return True
