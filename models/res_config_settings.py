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
import time
from urllib.request import urlopen
from odoo import http
from odoo.http import request
import time
import logging


class ResConfigSettings(models.TransientModel):
      _inherit = 'res.config.settings'

      module_pos_netpay = fields.Boolean(string="Payment Netpay",config_parameter='pos_netpay_connector.module_pos_netpay',help="The transactions are processed by paym.")


      def set_values(self):
             super(ResConfigSettings, self).set_values()
             payment_methods = self.env['pos.payment.method']
             if not self.env['ir.config_parameter'].sudo().get_param('pos_terminal_name.module_pos_netpay'):
                    payment_methods |= payment_methods.search([('use_payment_terminal', '=', 'netpay')])
                    payment_methods.write({'use_payment_terminal': False})
