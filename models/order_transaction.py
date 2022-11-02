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


class PosOrderT(models.Model):
    _name = 'netpay.transaction'

    name = fields.Char('Nombre')
    payid = fields.Char('payid')
