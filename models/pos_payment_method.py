# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('netpay', 'netpay')]

    # Campos para Netpay
    netpay_test_mode = fields.Boolean("Test Mode", help='Run transactions in the test environment.')
    netpay_api_base = fields.Char("Netpay API Base", help="Base URL del API de Netpay (p.ej. https://suite.netpay.com.mx)")
    netpay_latest_response = fields.Text(copy=False)
    netpay_latest_diagnosis = fields.Char(copy=False)
    netpay_terminal_identifier = fields.Char('Terminal identifier', copy=False)
    # credenciales/terminal
    terminal_api_key = fields.Char('API Key')
    terminal_api_pwd = fields.Char('API Password')
    terminal_id = fields.Char('Terminal ID')
    administrators_only = fields.Boolean(string="Solo administradores", default=False)

    def proxy_netpay_request(self, data, operation='sale'):
        """RPC llamado desde el JS: delega en la función privada."""
        for pm in self:
            pm.ensure_one()
        return self._proxy_netpay_request_direct(data, operation)

    def _get_netpay_endpoint(self, operation):
        base = self.netpay_api_base or "https://suite.netpay.com.mx"
        if operation == 'sale':
            return f"{base}/gateway/integration-service/transactions/sale"
        if operation == 'cancel':
            return f"{base}/gateway/integration-service/transactions/cancel"
        if operation == 'reprint':
            return f"{base}/gateway/integration-service/transactions/reprint"
        # por defecto
        return f"{base}/gateway/integration-service/transactions/{operation}"

    def _proxy_netpay_request_direct(self, data, operation='sale'):
        """Hace el request a Netpay. Devuelve True en éxito o diccionario con 'error'."""
        self.ensure_one()
        TIMEOUT = 10
        try:
            endpoint = self._get_netpay_endpoint(operation)
            # Buscar token en traceability (por tu implementación)
            access_token = False
            if 'traceability' in data and isinstance(data['traceability'], dict):
                access_token = data['traceability'].get('access_token') or data['traceability'].get('refresh_token')
            headers = {
                'Content-Type': 'application/json',
            }
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'

            # Construir payload especialmente para sale/cancel/reprint si quieres
            json_data = data

            _logger.info("Netpay request %s %s %s", operation, endpoint, json_data)
            req = requests.post(endpoint, data=json.dumps(json_data), headers=headers, timeout=TIMEOUT)
            _logger.info("Netpay response status: %s", req.status_code)

            if req.status_code == 200:
                # Si no hay contenido, devolver True
                if not req.content:
                    return True
                try:
                    response_json = req.json()
                    return response_json
                except Exception:
                    # devolver raw
                    return {'result': req.text}
            else:
                # intentar parsear error JSON
                try:
                    err = req.json()
                    if 'error_description' in err:
                        return {'error': {'status_code': req.status_code, 'message': err['error_description']}}
                    elif 'message' in err:
                        return {'error': {'status_code': req.status_code, 'message': err['message']}}
                    else:
                        return {'error': {'status_code': req.status_code, 'message': json.dumps(err)}}
                except Exception:
                    return {'error': {'status_code': req.status_code, 'message': req.text}}
        except requests.exceptions.RequestException as e:
            _logger.exception("Error al conectar con Netpay: %s", e)
            return {'error': {'status_code': 0, 'message': str(e)}}