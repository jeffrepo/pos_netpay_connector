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


    # @http.route('/web/pos/transactions', type='json', methods=['POST'],auth='none')
    # def get_sessions(self, **post):
    #     sessions_rec = request.env["pos.session"].sudo().search([])
    #     logging.warning('EXTERNAL NETPAY CONECTION')
    #
    #     logging.warning(post)
    #
    #     sessions = []
    #     for session in sessions_rec:
    #         sessions.append({
    #             "id": session.id,
    #             "name": session.name
    #         })
    #     if post:
    #         if ("folioNumber" and "internalNumber" and "listOfPays" and "totalAmount") in post:
    #             data = {"code": "00","message": "Recibido"}
    #         else:
    #             data = {"code": "400", "message": "fail"}
    #
    #
    #     return data


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
#     @http.route('/pos/web?config_id=1#cids=1', type='json', methods=['POST'],auth='none', csrf=False)
    def get_sessions(self):

        logging.warning('EXTERNAL NETPAY CONECTION HTTP')
        json_data = json.loads(request.httprequest.data)
        logging.warning(json_data)

        data = {"code": 300, "message": "error"}
        list_keys = ["folioNumber", "internalNumber", "tableId", "listOfPays", "tipTotalAmount", "totalAmount"]
        if ("responseCode" in json_data) and ("traceability" in json_data) and ("type" in json_data["traceability"]) and (json_data["traceability"]["type"] == "sale") and ("terminalId" not in json_data) and ("serial_number" in json_data["traceability"]):
            payment_method = request.env['pos.payment.method'].sudo().search([('netpay_terminal_identifier', '=', json_data['traceability']['serial_number'])], limit=1)
            logging.warning('Cancelada por el usuario')
            data = {"code": "00", "message": "Recibido"}
            payment_method.netpay_latest_response = json.dumps(json_data)

#         if ("folioNumber" and "internalNumber" and "tableId" and "listOfPays" and "tipTotalAmount" and "totalAmount") in json_data:
#             data = {"code": "00", "message": "Recibido"}
#             logging.warning('main 1')

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

#     @http.route('/web/pos/transactions', type='json', methods=['POST'],auth='none', csrf=False)
#     def get_sessions(self):

#         logging.warning('EXTERNAL NETPAY CONECTION HTTP')
#         json_data = json.loads(request.httprequest.data)
#         logging.warning(json_data)



#         order_id = request.env['pos.order'].sudo().search([('id','=', 159 )])
#         logging.warning('PEIDODOD')
#         logging.warning(order_id)
#         data = {"code": 300, "message": "error"}
#         if "orderId" in json_data and "folioNumber" in json_data:
#             trans_id = request.env['netpay.transaction'].sudo().create({'name': json_data['folioNumber'], 'payid': json_data['orderId']})
#             logging.warning(trans_id)
#             pos_reference = "Orden "+json_data['folioNumber']
#             orders_rec = request.env["pos.order"].sudo().search([("pos_reference",'=', pos_reference)])
#             logging.warning('si hay')
#             logging.warning(orders_rec)
#             if orders_rec:
#                 intento = 0
#                 logging.warning('ORDERS_REC')
#                 logging.warning(orders_rec)
#                 orders_rec.write({'order_neypay_id': json_data['orderId'] })
#                 orders_rec.order_neypay_id = json_data['orderId']
#                 orders_rec.update({'order_neypay_id': json_data['orderId']})
#                 data = {"code": "00", "message": "Recibido"}

#                 logging.warning(json_data['traceability'])
#                 if len(json_data['traceability']) > 0 and  "cancel" in json_data['traceability'] and json_data['traceability']['cancel']:
#                     logging.warning('entro a asignacion de anulacion')
#                     orders_rec.write({'netpaystatus': "cancel"})
#                     orders_rec.netpaystatus = "cancel"

#                 if len(json_data['traceability']) > 0 and  "reprint" in json_data['traceability'] and json_data['traceability']['reprint']:
#                     orders_rec.write({'reprint_netpay': True})

#         logging.warning(request.httprequest)
#         logging.warning('--after alll')

#         headers = {'Content-Type': 'application/json'}
#         request._json_response = self.alternative_json_response.__get__(request, JsonRequest)
#         return data

#     #@http.route('/web/dataset/call_kw/pos.order/sale_netpay_ui/transactions', type='json', methods=['POST'],auth='none', csrf=False)
#     #def get_sessions(self):
#         #sessions_rec = request.env["pos.session"].sudo().search([])
#         #logging.warning('EXTERNAL NETPAY CONECTION HTTP')
#         #logging.warning(json.loads(request.httprequest.data))
#         #logging.warning(request.httprequest)
#         #logging.warning('--after alll')
#         #sessions = []
#         #data = {"code": "00", "message": "Recibido"}
#         #for session in sessions_rec:
#         #    sessions.append({
#         #        "id": session.id,
#         #        "name": session.name
#         #    })

#         #return json.dumps(data)



#     @http.route('/mrp/upload_attachment', type='http', methods=['POST'], auth="user")
#     def upload_document(self, ufile, **kwargs):
#         files = request.httprequest.files.getlist('ufile')
#         result = {'success': _("All files uploaded")}
#         for ufile in files:
#             try:
#                 mimetype = ufile.content_type
#                 request.env['mrp.document'].create({
#                     'name': ufile.filename,
#                     'res_model': kwargs.get('res_model'),
#                     'res_id': int(kwargs.get('res_id')),
#                     'mimetype': mimetype,
#                     'datas': base64.encodebytes(ufile.read()),
#                 })
#             except Exception as e:
#                 logger.exception("Fail to upload document %s" % ufile.filename)
#                 result = {'error': str(e)}

#         return json.dumps(result)


    # {'affiliation': '7389108', 'applicationLabel': 'Debit Mastercard', 'arqc': '2139859B15BAAFD8', 'aid': 'A0000000041010', 'amount': '1.0', 'authCode': '222222', 'bankName': 'SANTANDER', 'bin': '557907', 'cardExpDate': '10/26', 'cardType': 'D', 'cardTypeName': 'MASTERCARD', 'cityName': 'Guadalupe NUEVO LEON', 'responseCode': '00', 'folioNumber': '00042-011-0005', 'hasPin': True, 'hexSign': '', 'isQps': 0, 'isRePrint': False, 'message': 'Transacción exitosa', 'moduleCharge': '5', 'moduleLote': '1', 'customerName': 'TRADICIONAL              /', 'terminalId': '1491040497', 'orderId': '221008112445-1491040497', 'preAuth': '0', 'preStatus': 0, 'promotion': '00', 'rePrintDate': '1.3.6.3.p.p_20220831', 'rePrintMark': 'MASTER', 'reprintModule': 'C', 'cardNumber': '6039', 'storeName': 'CICAP', 'streetName': 'AVE PABLO LIVAS 7200', 'ticketDate': 'OCT. 08, 22 11:24:44 ', 'tipAmount': '0.0', 'tipLessAmount': '1.0', 'traceability': {'ordenId': '', 'idProducto': '00042-011-0005', 'idTienda': 9194}, 'transDate': '2022-10-08 11:24:47.CDT', 'transType': 'A', 'transactionCertificate': '3A91A0FD7FD4670E', 'transactionId': 'EC817201-0FC8-AD70-4730-15CA2D6E4AEA'}
