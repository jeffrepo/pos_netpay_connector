# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging
from datetime import datetime
import requests

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    order_netpay_id = fields.Char("orderId netpay")
    netpaystatus = fields.Char('Status netpay')
    reprint_netpay = fields.Boolean('Reprint netpay')
    order_cancel_netpay = fields.Boolean('Orden cancelada')
    cancel_hour = fields.Datetime('Fecha y hora de cancelación')
    reprint_time = fields.Datetime('Fecha y hora última reimpresión')

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(PosOrder, self).create_from_ui(orders, draft)
        # Mantener la lógica previa: si se envía netpay_orderId desde el frontend guardarlo
        try:
            if res and res[0]['id'] > 0:
                order = self.browse(res[0]['id'])
                if orders and orders[0] and 'data' in orders[0] and 'netpay_orderId' in orders[0]['data']:
                    netpay_order = orders[0]['data']['netpay_orderId']
                    if isinstance(netpay_order, dict) and 'orderId' in netpay_order:
                        order.order_netpay_id = netpay_order['orderId']
        except Exception:
            _logger.exception("Error guardando order_netpay_id en create_from_ui")
        return res

    def cancel_order_netpay(self):
        self.ensure_one()
        if not self.order_netpay_id:
            raise UserError(_('No hay order_netpay_id para cancelar en Netpay.'))
        config = self.session_id.config_id
        endpoint = config.netpay_api_base or "https://suite.netpay.com.mx"
        url = f"{endpoint}/gateway/integration-service/transactions/cancel"
        payload = {
            "traceability": {"cancel": True, "refresh_token": config.access_token if config else False},
            "serialNumber": str(config.serial_number) if config else '',
            "orderId": str(self.order_netpay_id),
            "storeId": str(config.store_id_netpay) if config else '',
        }
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (config.access_token or '')}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code != 200:
                raise UserError(_('Error al cancelar en Netpay: %s') % response.text)
        except Exception as e:
            raise UserError(_('Error de conexión con Netpay: %s') % str(e))
        # marcar orden cancelada localmente
        self.order_cancel_netpay = True
        self.cancel_hour = datetime.now()
        return True

    def reprint_order_netpay(self):
        self.ensure_one()
        if not self.order_netpay_id:
            raise UserError(_('No hay order_netpay_id para reimprimir en Netpay.'))
        config = self.session_id.config_id
        endpoint = config.netpay_api_base or "https://suite.netpay.com.mx"
        url = f"{endpoint}/gateway/integration-service/transactions/reprint"
        payload = {
            "traceability": {"reprint": True, "refresh_token": config.access_token if config else False, "type": "reprint"},
            "orderId": str(self.order_netpay_id),
            "serialNumber": str(config.serial_number) if config else '',
            "storeId": str(config.store_id_netpay) if config else '',
        }
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (config.access_token or '')}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code != 200:
                raise UserError(_('Error en reprint Netpay: %s') % response.text)
        except Exception as e:
            raise UserError(_('Error de conexión con Netpay: %s') % str(e))
        self.reprint_netpay = True
        self.reprint_time = datetime.now()
        return True