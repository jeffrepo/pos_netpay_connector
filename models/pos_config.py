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

class PosConfig(models.Model):
    _inherit = 'pos.config'

    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    serial_number = fields.Char('Serial number')
    store_id_netpay = fields.Char('Store id netpay')

    def netpay_connection(self, extra_info):
        logging.warning('test')

        payload = ""

        url = "https://suite.netpay.com.mx/gateway/oauth-service/oauth/token"
        #url = "https://api-154.api-netpay.com/oauth-service/oauth/token"
        if 'new_token' in extra_info:
            #payload = 'grant_type=password&username=smartPos&password=netpay'
            payload = 'grant_type=password&username=Nacional&password=netpay'
            #payload = 'grant_type=password&username=trusted-app&password=netpay'
        if 'refresh_token' in extra_info:
            payload = 'grant_type=refresh_token&refresh_token='+str(extra_info['refresh_token'])
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Basic dHJ1c3RlZC1hcHA6c2VjcmV0'
        }
        # auth=HTTPBasicAuth('trusted-app', 'secret')
        response = requests.post(url, data = payload, headers = headers)
        logging.warning("netpay_connection POS CONFIG")
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
                    value = self.get_first_token()
                    logging.warning('lowwwwwwwwwwwwwwwwwwwwwwww')
                    logging.warning(value)
                    if value == True:
                        self.get_refresh_token()
                    else:
                        raise UserError(response_content)
        return True

    def get_first_token(self):
        self.netpay_connection({'new_token'})
        return True

    def get_refresh_token(self):
        self.netpay_connection({'refresh_token': self.refresh_token})
        return True

    def activate_token_netapy(self):
        logging.warning('Acción automatizada')
        points_of_sale = self.env['pos.config'].search([
            ('access_token', '!=', False),
            ('serial_number', '!=', False),
            ('refresh_token', '!=', False),
            ('store_id_netpay', '!=', False)])
        logging.warning(points_of_sale)
        for point in points_of_sale:
            logging.warning('punto')
            logging.warning(point.name)
            point.get_refresh_token()
            logging.warning('Se ha llegado más lejos de refrescar el token ;D')
        return True
