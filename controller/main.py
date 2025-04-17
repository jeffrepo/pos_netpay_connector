import base64
import json
import logging

from odoo import http

from odoo.http import request, Response, JsonRequest
from odoo.tools.translate import _
from odoo.tools import date_utils
import logging
import requests
_logger = logging.getLogger(__name__)

class PosRoute(http.Controller):

    def alternative_json_response(self, result=None, error=None):
        if error is not None:
            response = error
        if result is not None:
            response = result
        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)
        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )

    @http.route('/web/pos/transactions', type='json', methods=['POST'],auth='none', csrf=False)
    def get_sessions(self):

        logging.warning('EXTERNAL NETPAY CONECTION HTTP')
        json_data = json.loads(request.httprequest.data)
        logging.warning(json_data)

        data = {"code": 300, "message": "error"}
        list_keys = ["folioNumber", "internalNumber", "tableId", "listOfPays", "tipTotalAmount", "totalAmount"]
        if ("orderId" not in json_data) and ("traceability" in json_data) and ("terminalId" in json_data) and ("responseCode" in json_data):
            payment_method = request.env['pos.payment.method'].sudo().search([('netpay_terminal_identifier', '=', json_data['traceability']['serial_number'])], limit=1)
            data = {"code": "00", "message": "Recibido"}
            payment_method.netpay_latest_response = json.dumps(json_data)
        if ("terminalId" in json_data) and ("responseCode" in json_data) and (json_data["responseCode"] == "02"):
            payment_method = request.env['pos.payment.method'].sudo().search([('netpay_terminal_identifier', '=', json_data['traceability']['serial_number'])], limit=1)
            data = {"code": "00", "message": "Recibido"}
            payment_method.netpay_latest_response = json.dumps(json_data)
        if ("responseCode" in json_data) and ("traceability" in json_data) and ("type" in json_data["traceability"]) and (json_data["traceability"]["type"] == "sale") and ("terminalId" not in json_data) and ("serial_number" in json_data["traceability"]):
            payment_method = request.env['pos.payment.method'].sudo().search([('netpay_terminal_identifier', '=', json_data['traceability']['serial_number'])], limit=1)
            logging.warning('Cancelada por el usuario')
            data = {"code": "00", "message": "Recibido"}
            payment_method.netpay_latest_response = json.dumps(json_data)

        if "orderId" in json_data and "folioNumber" in json_data and 'terminalId' in json_data:
            payment_method = request.env['pos.payment.method'].sudo().search([('netpay_terminal_identifier', '=', json_data['terminalId'])], limit=1)
            logging.warning('main 2')
            if payment_method:
                payment_method.netpay_latest_response = False
                if json_data['orderId']:
                    if "traceability" in json_data and "cancel" in json_data["traceability"] and json_data["traceability"]["cancel"] == True:
                        orders = request.env['pos.order'].sudo().search([('order_netpay_id', '=', json_data['orderId'])])
                        logging.warning('Se encontro alguna orden?')
                        logging.warning(orders)
                        if orders:
                            data = {"code": "00", "message": "Recibido"}
                            orders.order_cancel_netpay = True
                        else:
                            data = {"code": 300, "message": "Orden no encontrada"}
                    if "traceability" in json_data and "type" in json_data["traceability"] and json_data["traceability"]["type"] == 'reprint':
                        orders = request.env['pos.order'].sudo().search([('order_netpay_id', '=', json_data['orderId'])])
                        logging.warning('Se encontro alguna orden?')
                        logging.warning(orders)
                        if orders:
                            data = {"code": "00", "message": "Recibido"}
                            orders.order_cancel_netpay = True
                        else:
                            data = {"code": 300, "message": "Orden no encontrada "}
                    if "traceability" in json_data and "type" in json_data["traceability"] and json_data["traceability"]["type"] == 'sale':
                        data = {"code": "00", "message": "Recibido"}
                        payment_method.netpay_latest_response = json.dumps(json_data)
                        payment_method.netpay_latest_diagnosis = json_data['orderId']

                    logging.warning('Que da data?')
                    logging.warning(data)
                else:
                    data = {"code": "00", "message": "Recibido"}
                    payment_method.netpay_latest_response = json.dumps(json_data)
            else:
                _logger.error('received a message for a terminal not registered in Odoo: PARa mientras')

        logging.warning(request.httprequest)
        logging.warning('--after alll')

        headers = {'Content-Type': 'application/json'}
        request._json_response = self.alternative_json_response.__get__(request, JsonRequest)
        logging.warning('Devolviendo el ultimo data')
        logging.warning(data)
        return data