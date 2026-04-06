# -*- coding: utf-8 -*-
import json
import logging
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessDenied

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    netpay_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    netpay_latest_response = fields.Char(copy=False, groups='base.group_erp_manager')
    netpay_latest_diagnosis = fields.Char(copy=False)
    netpay_terminal_identifier = fields.Char(copy=False)

    terminal_api_key = fields.Char('API Key')
    terminal_api_pwd = fields.Char('API Password')
    terminal_id = fields.Char('Terminal ID')
    administrators_only = fields.Boolean(string="Solo administradores", default=False)

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('netpay', 'Netpay')]

    @api.model
    def _load_pos_data_fields(self, config):
        params = super()._load_pos_data_fields(config)
        params += [
            'netpay_terminal_identifier',
            'terminal_id',
            'administrators_only',
        ]
        return params

    def _is_write_forbidden(self, fields):
        return super()._is_write_forbidden(fields - {'netpay_latest_response', 'netpay_latest_diagnosis'})

    def get_latest_netpay_status(self):
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessDenied()

        latest_response = self.sudo().netpay_latest_response
        return json.loads(latest_response) if latest_response else False

    def proxy_netpay_request(self, data, operation=False):
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessDenied()
        if not data:
            raise UserError(_('Invalid Netpay request'))

        if operation == 'sale':
            self.sudo().netpay_latest_response = ''

        return self._proxy_netpay_request_direct(data, operation or 'sale')

    def _get_netpay_endpoints(self):
        return {
            'sale': 'https://suite.netpay.com.mx/gateway/integration-service/transactions/sale',
            'cancel': 'https://suite.netpay.com.mx/gateway/integration-service/transactions/cancel',
            'reprint': 'https://suite.netpay.com.mx/gateway/integration-service/transactions/reprint',
        }

    def _proxy_netpay_request_direct(self, data, operation):
        self.ensure_one()
        timeout = 10

        endpoint = self._get_netpay_endpoints()[operation]
        access_token = data.get('traceability', {}).get('access_token') or data.get('traceability', {}).get('refresh_token')

        headers = {
            'Content-Type': 'application/json',
        }
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'

        _logger.info('Request to Netpay by user #%d: %s', self.env.uid, data)

        req = requests.post(endpoint, json=data, headers=headers, timeout=timeout)

        if req.status_code == 401:
            return {
                'error': {
                    'status_code': req.status_code,
                    'message': req.text,
                }
            }

        if req.text == 'ok':
            return True

        try:
            return req.json()
        except Exception:
            if req.status_code == 200:
                return True
            return {
                'error': {
                    'status_code': req.status_code,
                    'message': req.text,
                }
            }
