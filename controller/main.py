import base64
import json
import logging

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import logging
logger = logging.getLogger(__name__)


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





    @http.route('/web/pos/transactions', type='json', methods=['POST'],auth='none', csrf=False)
    def get_sessions(self):
        sessions_rec = request.env["pos.session"].sudo().search([])
        logging.warning('EXTERNAL NETPAY CONECTION HTTP')
        logging.warning(json.loads(request.httprequest.data))
        logging.warning(request.httprequest)
        logging.warning('--after alll')
        sessions = []
        data = {"code": "00", "message": "Recibido"}
        for session in sessions_rec:
            sessions.append({
                "id": session.id,
                "name": session.name
            })

        return json.dumps(data)



    @http.route('/mrp/upload_attachment', type='http', methods=['POST'], auth="user")
    def upload_document(self, ufile, **kwargs):
        files = request.httprequest.files.getlist('ufile')
        result = {'success': _("All files uploaded")}
        for ufile in files:
            try:
                mimetype = ufile.content_type
                request.env['mrp.document'].create({
                    'name': ufile.filename,
                    'res_model': kwargs.get('res_model'),
                    'res_id': int(kwargs.get('res_id')),
                    'mimetype': mimetype,
                    'datas': base64.encodebytes(ufile.read()),
                })
            except Exception as e:
                logger.exception("Fail to upload document %s" % ufile.filename)
                result = {'error': str(e)}

        return json.dumps(result)


    # {'affiliation': '7389108', 'applicationLabel': 'Debit Mastercard', 'arqc': '2139859B15BAAFD8', 'aid': 'A0000000041010', 'amount': '1.0', 'authCode': '222222', 'bankName': 'SANTANDER', 'bin': '557907', 'cardExpDate': '10/26', 'cardType': 'D', 'cardTypeName': 'MASTERCARD', 'cityName': 'Guadalupe NUEVO LEON', 'responseCode': '00', 'folioNumber': '00042-011-0005', 'hasPin': True, 'hexSign': '', 'isQps': 0, 'isRePrint': False, 'message': 'Transacción exitosa', 'moduleCharge': '5', 'moduleLote': '1', 'customerName': 'TRADICIONAL              /', 'terminalId': '1491040497', 'orderId': '221008112445-1491040497', 'preAuth': '0', 'preStatus': 0, 'promotion': '00', 'rePrintDate': '1.3.6.3.p.p_20220831', 'rePrintMark': 'MASTER', 'reprintModule': 'C', 'cardNumber': '6039', 'storeName': 'CICAP', 'streetName': 'AVE PABLO LIVAS 7200', 'ticketDate': 'OCT. 08, 22 11:24:44 ', 'tipAmount': '0.0', 'tipLessAmount': '1.0', 'traceability': {'ordenId': '', 'idProducto': '00042-011-0005', 'idTienda': 9194}, 'transDate': '2022-10-08 11:24:47.CDT', 'transType': 'A', 'transactionCertificate': '3A91A0FD7FD4670E', 'transactionId': 'EC817201-0FC8-AD70-4730-15CA2D6E4AEA'}
