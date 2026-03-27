# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class PosRoute(http.Controller):

    def alternative_json_response(self, result=None, error=None):
        response = result if error is None else error
        body = json.dumps(response)
        return Response(
            body,
            status=200,
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/web/pos/transactions', type='json', methods=['POST'], auth='none', csrf=False)
    def get_sessions(self):
        try:
            json_data = json.loads(request.httprequest.data)
        except Exception:
            _logger.exception("Invalid JSON payload")
            return {"code": 400, "message": "Invalid JSON"}

        data = {"code": 300, "message": "error"}

        try:
            if ("orderId" not in json_data) and ("traceability" in json_data) and ("terminalId" in json_data) and ("responseCode" in json_data):
                payment_method = request.env['pos.payment.method'].sudo().search([
                    ('id', '=', int(json_data['traceability']['payment_method_id']))
                ], limit=1)
                data = {"code": "00", "message": "Recibido"}
                payment_method.netpay_latest_response = json.dumps(json_data)

            if ("terminalId" in json_data) and ("responseCode" in json_data) and (json_data["responseCode"] == "02"):
                payment_method = request.env['pos.payment.method'].sudo().search([
                    ('id', '=', int(json_data['traceability']['payment_method_id']))
                ], limit=1)
                data = {"code": "00", "message": "Recibido"}
                payment_method.netpay_latest_response = json.dumps(json_data)

            if (
                ("responseCode" in json_data)
                and ("traceability" in json_data)
                and ("type" in json_data["traceability"])
                and (json_data["traceability"]["type"] == "sale")
                and ("terminalId" not in json_data)
                and ("serial_number" in json_data["traceability"])
            ):
                payment_method = request.env['pos.payment.method'].sudo().search([
                    ('id', '=', int(json_data['traceability']['payment_method_id']))
                ], limit=1)
                data = {"code": "00", "message": "Recibido"}
                payment_method.netpay_latest_response = json.dumps(json_data)

            if "orderId" in json_data and "folioNumber" in json_data and 'terminalId' in json_data:
                payment_method = request.env['pos.payment.method'].sudo().search([
                    ('id', '=', int(json_data['traceability']['payment_method_id']))
                ], limit=1)

                if payment_method:
                    payment_method.netpay_latest_response = False

                    if json_data['orderId']:
                        if "traceability" in json_data and json_data["traceability"].get("cancel") is True:
                            orders = request.env['pos.order'].sudo().search([
                                ('order_netpay_id', '=', json_data['orderId'])
                            ])
                            if orders:
                                data = {"code": "00", "message": "Recibido"}
                                orders.order_cancel_netpay = True
                            else:
                                data = {"code": 300, "message": "Orden no encontrada"}

                        elif "traceability" in json_data and json_data["traceability"].get("type") == 'reprint':
                            orders = request.env['pos.order'].sudo().search([
                                ('order_netpay_id', '=', json_data['orderId'])
                            ])
                            if orders:
                                data = {"code": "00", "message": "Recibido"}
                                orders.reprint_netpay = True
                            else:
                                data = {"code": 300, "message": "Orden no encontrada"}

                        elif "traceability" in json_data and json_data["traceability"].get("type") == 'sale':
                            data = {"code": "00", "message": "Recibido"}
                            payment_method.netpay_latest_response = json.dumps(json_data)
                            payment_method.netpay_latest_diagnosis = json_data['orderId']
                    else:
                        data = {"code": "00", "message": "Recibido"}
                        payment_method.netpay_latest_response = json.dumps(json_data)

        except Exception:
            _logger.exception("Error processing Netpay notification")
            return {"code": 500, "message": "Internal server error"}

        return data