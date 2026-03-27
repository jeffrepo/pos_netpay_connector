odoo.define('pos_netpay_connector.netpay_payment', function(require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const rpc = require('web.rpc');
    const { Gui } = require('point_of_sale.Gui');
    const core = require('web.core');
    const _t = core._t;

    const NetpayPayment = PaymentInterface => class extends PaymentInterface {

        async send_payment_request(cid) {
            if (this._super) {
                this._super(...arguments);
            }
            const order = this.pos.get_order();
            const line = order.selected_paymentline;

            if (line.get_payment_status && (line.get_payment_status() === 'retry' || line.get_payment_status() === 'force_done')) {
                if (line.set_payment_status) {
                    line.set_payment_status('pending');
                }
            }

            const data = this._netpay_pay_data();

            try {
                const result = await rpc.query({
                    model: 'pos.payment.method',
                    method: 'proxy_netpay_request',
                    args: [[this.payment_method.id], data, 'sale'],
                }, {
                    timeout: 5500,
                    shadow: true,
                });
                return this._netpay_handle_response(result);
            } catch (err) {
                return this._handle_odoo_connection_failure(err);
            }
        }

        _netpay_pay_data() {
            const order = this.pos.get_order();
            const config = this.pos.config;
            const line = order.selected_paymentline;
            const serial_number = config.serial_number || false;
            const store_id = config.store_id_netpay || false;
            const config_id = config.id || false;
            const access_token = config.access_token || false;
            const payment_method_id = line.payment_method ? line.payment_method.id : 0;
            const terminalId = line.payment_method ? line.payment_method.terminal_id : 0;

            return {
                'serialNumber': serial_number,
                'amount': line.amount,
                'storeId': store_id,
                'folioNumber': order.uid + "-" + line.cid,
                'msi': "",
                "traceability": {
                    'access_token': access_token,
                    'type': "sale",
                    'config_id': config_id,
                    'serial_number': serial_number,
                    'payment_method_id': payment_method_id,
                    'terminalId': terminalId,
                }
            };
        }

        _handle_odoo_connection_failure(err) {
            const line = this.pending_netpay_line();
            if (line && line.set_payment_status) {
                line.set_payment_status('retry');
            }
            this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'));
            return Promise.reject(err);
        }

        _show_error(msg, title) {
            if (!title) {
                title = _t('NETPAY Error');
            }
            Gui.showPopup('ErrorPopup', {
                'title': title,
                'body': msg,
            });
        }

        pending_netpay_line() {
            return this.pos.get_order().paymentlines.find(
                paymentLine => paymentLine.payment_method && paymentLine.payment_method.use_payment_terminal === 'netpay' && (!paymentLine.is_done())
            );
        }

        _netpay_handle_response(response) {
            const line = this.pos.get_order().selected_paymentline;
            if (!response) {
                this._show_error(_t('Empty response from server'));
                return Promise.resolve();
            }
            if (response.error && response.error.status_code != 200) {
                this._show_error(_t(response.error.message.toString()));
                if (line && line.set_payment_status) line.set_payment_status('force_done');
                return Promise.resolve();
            }
            if (response === true || (response && response.SaleToPOIRequest)) {
                if (line && line.set_payment_status) line.set_payment_status('waitingCard');
                return this._start_polling_for_response();
            } else {
                this._show_error(_t('Unexpected response from Netpay'));
                return Promise.resolve();
            }
        }

        _start_polling_for_response() {
            const self = this;
            return new Promise(function(resolve, reject) {
                self.remaining_polls = 6;
                self._poll_interval = setInterval(function() {
                    self._poll_for_response(resolve, reject);
                }, 5500);
            }).finally(function() {
                clearInterval(self._poll_interval);
            });
        }

        _poll_for_response(resolve, reject) {
            const line = this.pending_netpay_line();
            const order = this.pos.get_order();
            const folio = order.uid + "-" + (line ? line.cid : "");
            const self = this;

            return rpc.query({
                model: 'pos.payment.method',
                method: 'get_latest_netpay_status',
                args: [[this.payment_method.id], this._netpay_get_sale_id(), folio],
            }, {
                timeout: 5500,
                shadow: false,
            }).catch((err) => {
                if (self.remaining_polls != 0) {
                    self.remaining_polls--;
                    return Promise.reject(err);
                } else {
                    self.poll_error_order = self.pos.get_order();
                    if (line && line.set_payment_status) line.set_payment_status('retry');
                    return self._handle_odoo_connection_failure(err);
                }
            }).then(function(status) {
                const notification = status.latest_response;
                if (notification && notification.folioNumber == folio) {
                    if (notification.responseCode == '00') {
                        order.set_netpay_orderId(notification);
                        resolve(true);
                    } else {
                        const message = notification.message || "Error";
                        self._show_error(_.str.sprintf(_t('Message from Netpay: %s'), message));
                        if (line && line.set_payment_status) line.set_payment_status('retry');
                        reject();
                    }
                } else if (notification && notification.responseCode != "00") {
                    self._show_error(_.str.sprintf(_t(notification.message || 'Error')));
                    if (line && line.set_payment_status) line.set_payment_status('retry');
                    resolve(false);
                } else {
                    if (line && line.set_payment_status) line.set_payment_status('waitingCard');
                }
            });
        }

        _netpay_get_sale_id() {
            const config = this.pos.config;
            return `${config.display_name} (ID: ${config.id})`;
        }

    };

    Registries.Component.extend(PaymentInterface, NetpayPayment);
});