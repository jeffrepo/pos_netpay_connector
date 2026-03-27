# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
import json

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    serial_number = fields.Char('Serial number')
    store_id_netpay = fields.Char('Store id netpay')
    netpay_api_base = fields.Char('Netpay API Base', default='https://suite.netpay.com.mx')
    netpay_client_id = fields.Char('Netpay Client ID')
    netpay_client_secret = fields.Char('Netpay Client Secret')

    def netpay_connection(self, extra_info):
        """Solicitar token a Netpay: extra_info puede contener 'new_token' o 'refresh_token'"""
        self.ensure_one()
        url = f"{self.netpay_api_base}/gateway/oauth-service/oauth/token"
        payload = ''
        if 'new_token' in extra_info:
            # datos por defecto (ajusta según tu credencial)
            payload = 'grant_type=password&username=smartPos&password=netpay'
        if 'refresh_token' in extra_info:
            payload = 'grant_type=refresh_token&refresh_token=' + str(extra_info['refresh_token'])
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic dHJ1c3RlZC1hcHA6c2VjcmV0'
        }
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            _logger.info('Netpay token response: %s', response)
            if response.status_code == 200 and response.content:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data.get('access_token')
                if 'refresh_token' in data:
                    self.refresh_token = data.get('refresh_token')
                return True
            else:
                _logger.warning('Error al obtener token Netpay: %s', response.text)
                raise UserError(_('Error al obtener token Netpay: %s') % response.text)
        except requests.exceptions.RequestException as e:
            _logger.exception('Error netpay_connection: %s', e)
            raise UserError(_('Error de conexión con Netpay: %s') % str(e))

    def get_first_token(self):
        return self.netpay_connection({'new_token': True})

    def get_refresh_token(self):
        return self.netpay_connection({'refresh_token': self.refresh_token})

    def activate_token_netpay(self):
        configs = self.search([
            ('access_token', '!=', False),
            ('serial_number', '!=', False),
            ('refresh_token', '!=', False),
            ('store_id_netpay', '!=', False)
        ])
        for cfg in configs:
            try:
                cfg.get_refresh_token()
            except Exception:
                _logger.exception('No se pudo refrescar token para %s', cfg.id)
        return True