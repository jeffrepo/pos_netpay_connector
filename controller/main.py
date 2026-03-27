# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, Response, JsonRequest

_logger = logging.getLogger(__name__)


class PosNetpayController(http.Controller):

    def _json_response(self, result=None, error=None):
        body = json.dumps(result if error is None else error)
        return Response(body, status=200, headers=[('Content-Type', 'application/json')])

    @http.route('/pos_netpay/transactions', type='json', auth='none', methods=['POST'], csrf=False)
    def pos_netpay_transactions(self, **kw):
        """Endpoint moderno para recibir notificaciones de Netpay"""
        try:
            payload = request.httprequest.get_data(as_text=True)
            data = json.loads(payload)
        except Exception:
            _logger.exception("Payload JSON inválido en /pos_netpay/transactions")
            return {"code": 400, "message": "Invalid JSON"}

        # Validar estructura básica
        try:
            traceability = data.get('traceability', {})
            pm_id = None
            if isinstance(traceability, dict) and traceability.get('payment_method_id'):
                pm_id = int(traceability.get('payment_method_id'))
            elif data.get('traceability') and isinstance(data['traceability'], dict) and data['traceability'].get('payment_method_id'):
                pm_id = int(data['traceability']['payment_method_id'])

            if pm_id:
                payment_method = request.env['pos.payment.method'].sudo().browse(pm_id)
                if payment_method.exists():
                    payment_method.sudo().write({'netpay_latest_response': json.dumps(data)})
                    if 'orderId' in data and 'traceability' in data:
                        if data['traceability'].get('cancel'):
                            orders = request.env['pos.order'].sudo().search([('order_netpay_id', '=', data['orderId'])])
                            if orders:
                                orders.sudo().write({'order_cancel_netpay': True})
                                return {"code": "00", "message": "Recibido"}
                            else:
                                return {"code": 300, "message": "Orden no encontrada"}
                        if data['traceability'].get('type') == 'reprint':
                            orders = request.env['pos.order'].sudo().search([('order_netpay_id', '=', data['orderId'])])
                            if orders:
                                orders.sudo().write({'reprint_netpay': True})
                                return {"code": "00", "message": "Recibido"}
                            else:
                                return {"code": 300, "message": "Orden no encontrada"}
                        if data['traceability'].get('type') == 'sale':
                            payment_method.sudo().write({
                                'netpay_latest_response': json.dumps(data),
                                'netpay_latest_diagnosis': data.get('orderId') or False
                            })
                            return {"code": "00", "message": "Recibido"}
                    payment_method.sudo().write({'netpay_latest_response': json.dumps(data)})
                    return {"code": "00", "message": "Recibido"}
                else:
                    _logger.error('Mensaje recibido para un payment_method no existente: %s', pm_id)
                    return {"code": 404, "message": "Payment method not found"}
            else:
                _logger.warning('No se encontró payment_method_id en la notificación Netpay')
                return {"code": 300, "message": "No payment_method_id"}
        except Exception as e:
            _logger.exception('Error procesando notificación Netpay: %s', e)
            return {"code": 500, "message": "Internal Error"}