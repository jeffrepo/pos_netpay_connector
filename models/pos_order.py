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
from datetime import datetime
from urllib.request import urlopen
from odoo import http
from odoo.http import request
import time
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    order_netpay_id = fields.Char("orderId netpay")
    netpaystatus = fields.Char('Status netpay')
    reprint_netpay = fields.Boolean('Reprint netpay')
    order_cancel_netpay = fields.Boolean('Orden cancelada')
    cancel_hour = fields.Datetime('Fecha y hora de cancelación ')
    reprint_time = fields.Datetime('Fecha y hora última reimpresión')


    def delete_values(self, id):
        logging.warning('Ha limpiar la respuesta ')
        logging.warning(id[0])
        payment_methods = self.env['pos.payment.method'].search([('id', '=', id[0])])

        for payment_method in payment_methods:
            logging.warning(payment_method)
            payment_method.netpay_latest_response = ""
        return True

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(PosOrder, self).create_from_ui(orders, draft)
        logging.warning('EL RES')
        logging.warning(res)
        logging.warning(orders)

        logging.warning('SEARRCH create_from_ui ORDER POS NEW')
        if res and res[0]['id'] > 0:
            transaction = self.env['netpay.transaction'].search([])
            logging.warning('TRNSACTION UI')
            logging.warning(transaction)
            order_id = self.env['pos.order'].search([('id','=', res[0]['id'])])
            logging.warning('encontro orden')
            logging.warning(order_id)
            if order_id:
                logging.warning(order_id.order_netpay_id)
                if orders[0] and 'data' in orders[0] and 'netpay_orderId' in orders[0]['data'] and 'orderId' in orders[0]['data']['netpay_orderId']:
                    order_id.order_netpay_id = orders[0]['data']['netpay_orderId']['orderId']
        order_netpay = False
        intentos = 0
        return res


    def sale_netpay_ui(self, order):
        output = {'error': False, 'transaction': False}
        sesiones = self.env['pos.session'].search([('id', '=', order[0]['data']['pos_session_id'])])
        logging.warning('EL NETPAY')
        url = "https://quemen.odoo.com/web/dataset/call_kw/pos.order/sale_netpay_ui/transactions"
        response = requests.get(url)

        if sesiones:
            refresh_token_config = False
            serial_number = False
            store_id = sesiones.config_id.store_id_netpay
            for sesion in sesiones:
                if sesion.config_id.refresh_token != False:
                    refresh_token_config = sesion.config_id.access_token
                    serial_number = sesion.config_id.serial_number

            logging.warning('refresh_token')
            logging.warning(refresh_token_config)

            if refresh_token_config:

                logging.warning('test pos')

                payload = ""

                url = "https://suite.netpay.com.mx/gateway/integration-service/transactions/sale"
                #url = "https://api-154.api-netpay.com/integration-service/transactions/sale"
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
                                'msi': "",
                                "traceability": {
                                        "idProducto": '',
                                        "idTienda": store_id,
                                        "order_id":'',
                                        "serial_number":serial_number,
                                }
                            }



                            json_data['amount'] = order[0]['data']['amount_total']
                            json_data['folioNumber'] = order[0]['id']
                            json_data['traceability']['idProducto'] = order[0]['id']

                logging.warning('JSON NETPAYU')
                logging.warning(json_data)
                if json_data:

                    # # auth=HTTPBasicAuth('trusted-app', 'secret')
                    response = requests.post(url, data = json.dumps(json_data), headers = headers)
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

        url = "https://suite.netpay.com.mx/gateway/oauth-service/oauth/token"
        #url = "https://api-154.api-netpay.com/integration-service/oauth/token"
        if 'new_token' in extra_info:
            #payload = 'grant_type=password&username=smartPos&password=netpay'
            
            payload = 'grant_type=password&username=Nacional&password=netpay'
        if 'refresh_token' in extra_info:
            payload = 'grant_type=refresh_token&refresh_token='+str(extra_info['refresh_token'])
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Basic dHJ1c3RlZC1hcHA6c2VjcmV0'
        }
        # auth=HTTPBasicAuth('trusted-app', 'secret')
        response = requests.post(url, data = payload, headers = headers)
        logging.warning("GET TOKEN PY")
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

    def action_pos_order_cancel(self):
        logging.warning('Presionando al boton cancelar')
        logging.warning(self.cancel_hour)
        logging.warning(self.order_cancel_netpay)
        now = datetime.now()
        last_minute = 00
        last_hour = 00
        minute_difference = 00
        current_time = now.strftime("%H")
        logging.warning(now)
        if self.order_cancel_netpay == False:
            if self.cancel_hour != False:
                last_hour = self.cancel_hour.strftime('%H')
                last_minute = self.cancel_hour.strftime('%M')
                current_minute = now.strftime('%M')
                minute_difference = int(current_minute) - int(last_minute)

            if self.cancel_hour == False:
                logging.warning('La hora es false')
                self.cancel_hour = now.strftime("%Y-%m-%d %H:%M:%S")
                self.cancel_order_netpay()
                self.cancel_hour = now.strftime("%Y-%m-%d %H:%M:%S")

            elif self.cancel_hour != False and int(current_time) > int(last_hour):
                logging.warning('La hora es mayor')
                self.cancel_order_netpay()
                self.cancel_hour = now.strftime("%Y-%m-%d %H:%M:%S")
            elif self.cancel_hour != False and minute_difference > 2:
                logging.warning('2 minutos ya pasaron')
                self.cancel_order_netpay()
                self.cancel_hour = now.strftime("%Y-%m-%d %H:%M:%S")
            else:
                raise UserError('Por favor espere un momento')
        return True

    def cancel_order_netpay(self):
        logging.warning('Funcion cancel order')
        logging.warning('')
        now = datetime.now()

        url = "https://suite.netpay.com.mx/gateway/integration-service/transactions/cancel"

        refresh_token_config = False
        store_id = self.session_id.config_id.store_id_netpay
        order_uid = self.pos_reference[5:]
        order_uid = order_uid.replace(' ','')
        logging.warning('QUE es reference CANCEL')
        order_id = self.order_netpay_id

        if self.session_id.config_id.access_token:
            refresh_token_config = self.session_id.config_id.access_token
        logging.warning(order_id)

        serial_number = self.session_id.config_id.serial_number

#         payload = "{\r\n\"traceability\": {\"Ejemplo\":\"\"\r\n\t},\r\n  \"orderId\": \"{{orderId}}\",\r\n  \"serialNumber\": \"{{serialNumber}}\",\r\n  \"storeId\": \"{{storeId}}\"\r\n}"
        payload = {
            "traceability": {
                "cancel": True,
                "refresh_token": refresh_token_config
            },
            "serialNumber": str(serial_number),
            "orderId": str(order_id),
            "storeId": str(store_id),
        }

        logging.warning('payload')
        logging.warning(payload)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer '+str(refresh_token_config)
        }

        response = requests.post(url, data = json.dumps(payload), headers = headers)

        logging.warning('Response --------')
        logging.warning(response)
        logging.warning(response.content)
        logging.warning('')

        payment_method_id = self.env['pos.payment.method'].search([('netpay_terminal_identifier', '=', serial_number)])

        if payment_method_id:

            logging.warning('Entrando a los metodos de pago')
            logging.warning(payment_method_id)

            proxy_netpay_request = payment_method_id.proxy_netpay_request(payload, operation='cancel')
            logging.warning('Respuesta de proxy ::::')
            logging.warning(proxy_netpay_request)
            if proxy_netpay_request == True:
                latest_status = False

            logging.warning('Que es proxy_netpay_request cancel')
            logging.warning(proxy_netpay_request)
            if proxy_netpay_request != True and 'code' in proxy_netpay_request and 'message' in proxy_netpay_request:
                logging.warning('Error de prueba cancel')
                logging.warning(proxy_netpay_request)
                raise UserError(proxy_netpay_request['message'])

            elif proxy_netpay_request != True and 'error' in proxy_netpay_request and 'message' in proxy_netpay_request['error']:
                raise UserError(proxy_netpay_request['error']['message'])

            logging.warning('Creo que ya pasaste la parte woajaja')

        return True

    def action_pos_order_reprint(self):
        logging.warning('Boton para Reimprimir')
        now = datetime.now()
        last_minute = 0
        last_hour = 0
        minute_difference =0
        last_hour = 0
        current_time = now.strftime("%H")
        logging.warning(self.id)

        if self.reprint_time != False:
            last_hour = self.reprint_time.strftime("%H")
            last_minute = self.reprint_time.strftime("%M")
            current_minute = now.strftime("%M")
            minute_difference = int(current_minute) - int(last_minute)

        if self.reprint_time == False:
            logging.warning('Hora igual a False')
            self.reprint_time = now.strftime("%Y-%m-%d %H:%M:%S")
            self.reprint_order_netpay()
            self.reprint_time = now.strftime("%Y-%m-%d %H:%M:%S")

        elif self.reprint_time != False and int(current_time) > int(last_hour):
            logging.warning('Hora mayor reprint')
            logging.warning(self.reprint_time)
            self.reprint_order_netpay()
            self.reprint_time = now.strftime("%Y-%m-%d %H:%M:%S")
        elif self.reprint_time != False and minute_difference > 2:
            logging.warning('Minutos mayor reprint')
            self.reprint_order_netpay()
            self.reprint_time = now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise UserError('Por favor espere un momento')

        return True
    def reprint_order_netpay(self):
        now = datetime.now()
        logging.warning(' reprint_order_netpay reprint')
        if self.reprint_netpay == False:
            url = "https://suite.netpay.com.mx/gateway/integration-service/transactions/reprint"
            refresh_token_config = False
    #         payload = "{\r\n\"traceability\": {\"Ejemplo\":\"\"\r\n\t},\r\n  \"orderId\": \"{{orderId}}\",\r\n  \"serialNumber\": \"{{serialNumber}}\",\r\n  \"storeId\": \"{{storeId}}\"\r\n}"
            if self.session_id.config_id.access_token:
                refresh_token_config = self.session_id.config_id.access_token

            payload = {
                "traceability":{
                    "reprint": True,
                    "refresh_token": refresh_token_config,
                    "type":'reprint'
                },
                "orderId":'',
                "serialNumber":'',
                "storeId":'',
            }

            refresh_token_config = False
            if self.session_id.config_id.access_token:
                refresh_token_config = self.session_id.config_id.access_token

            headers = {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer '+str(refresh_token_config)
            }

            store_id = False
            order_id = False
            serial_number = False
            if self.session_id.config_id.serial_number:
                serial_number = self.session_id.config_id.serial_number
            if self.session_id.config_id.storeid:
                store_id = self.session_id.config_id.storeid

            if self.order_netpay_id:
                order_id = self.order_netpay_id
            payload["orderId"] = order_id
            payload["serialNumber"] = serial_number
            payload["storeId"] = store_id
    #         response = requests.request("POST", url, headers=headers, data = payload)
            response = requests.post(url, data = json.dumps(payload), headers = headers)
            logging.warning('Response reprint-----')
            logging.warning(response)
            logging.warning(response.content)
            payment_method_id = self.env['pos.payment.method'].search([('netpay_terminal_identifier', '=', serial_number)])

            if payment_method_id:

                logging.warning('Entrando a los metodos de pago')
                logging.warning(payment_method_id)
    #             model_payment = payment.payment_method_id

                proxy_netpay_request = payment_method_id.proxy_netpay_request(payload, operation='reprint')
                logging.warning('Respuesta de proxy ::::')
                logging.warning(proxy_netpay_request)
                if proxy_netpay_request == True:
                    latest_status = False

                logging.warning('Que es proxy_netpay_request reprint')
                logging.warning(proxy_netpay_request)
                if proxy_netpay_request != True and 'code' in proxy_netpay_request and 'message' in proxy_netpay_request:
                    logging.warning('Error de prueba')
                    logging.warning(proxy_netpay_request)
                    raise UserError(proxy_netpay_request['message'])
                elif proxy_netpay_request != True and 'error' in proxy_netpay_request and 'message' in proxy_netpay_request['error']:
                    raise UserError(proxy_netpay_request['error']['message'])

                logging.warning('Creo que ya pasaste la parte reprint woajaja')
        return True
