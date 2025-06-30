# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PosOrderT(models.Model):
    _name = 'netpay.transaction'
    _description = 'Netpay transaction'

    name = fields.Char('Nombre')
    payid = fields.Char('payid')
