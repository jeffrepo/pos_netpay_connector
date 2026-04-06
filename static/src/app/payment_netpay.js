/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";

export class PaymentNetpay extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentLineResolvers = {};
        this.pollingHandles = {};
    }

    sendPaymentRequest(uuid) {
        super.sendPaymentRequest(uuid);
        return this._netpayPay(uuid);
    }

    sendPaymentCancel(order, uuid) {
        super.sendPaymentCancel(order, uuid);
        return this._netpayCancel();
    }

    pendingNetpayLine() {
        return this.pos.getPendingPaymentLine("netpay");
    }

    _showError(msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: title || _t("Netpay Error"),
            body: msg,
        });
    }

    _handleOdooConnectionFailure(data = {}) {
        const line = this.pendingNetpayLine();
        if (line) {
            line.setPaymentStatus("retry");
        }
        this._showError(
            _t("Could not connect to the Odoo server, please check your internet connection and try again.")
        );
        return Promise.reject(data);
    }

    _callNetpay(data, operation = "sale") {
        return this.pos.data
            .silentCall("pos.payment.method", "proxy_netpay_request", [
                [this.payment_method_id.id],
                data,
                operation,
            ])
            .catch(this._handleOdooConnectionFailure.bind(this));
    }

    _netpayPayData(uuid) {
        const order = this.pos.getOrder();
        const line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);

        const folioNumber = `${order.uuid}--${line.uuid}`;

        if (line && line.setNetpayFolioNumber) {
            line.setNetpayFolioNumber(folioNumber);
        }

        return {
            serialNumber: this.pos.config.serial_number || this.payment_method_id.netpay_terminal_identifier || "",
            amount: line.amount,
            storeId: this.pos.config.store_id_netpay || "",
            folioNumber: folioNumber,
            msi: "",
            traceability: {
                type: "sale",
                access_token: this.pos.config.access_token || "",
                payment_method_id: this.payment_method_id.id,
                terminalId: this.payment_method_id.terminal_id || "",
                serial_number: this.pos.config.serial_number || this.payment_method_id.netpay_terminal_identifier || "",
            },
        };
    }

    _netpayPay(uuid) {
        const order = this.pos.getOrder();
        const line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);

        if (line.amount < 0) {
            this._showError(_t("Cannot process transactions with negative amount."));
            return Promise.resolve(false);
        }

        const data = this._netpayPayData(uuid);

        return this._callNetpay(data, "sale").then((response) => this._netpayHandleResponse(response, line));
    }

    _netpayCancel() {
        const line = this.pendingNetpayLine();
        if (!line) {
            return Promise.resolve(true);
        }

        const data = {
            serialNumber: this.pos.config.serial_number || "",
            orderId: line.transaction_id || "",
            storeId: this.pos.config.store_id_netpay || "",
            traceability: {
                cancel: true,
                refresh_token: this.pos.config.access_token || "",
                payment_method_id: this.payment_method_id.id,
                type: "cancel",
            },
        };

        return this._callNetpay(data, "cancel").then((response) => {
            if (response !== true && !response?.error) {
                this._showError(
                    _t("Cancelling the payment failed. Please cancel it manually on the payment terminal.")
                );
            }
            return true;
        });
    }

    _netpayHandleResponse(response, line) {
        if (!response) {
            this._showError(_t("Empty response from Netpay."));
            line.setPaymentStatus("force_done");
            return false;
        }

        if (response.error) {
            this._showError(response.error.message || _t("Unknown Netpay error."));
            line.setPaymentStatus("force_done");
            return false;
        }

        line.setPaymentStatus("waitingCard");
        return this.waitForPaymentConfirmation(line);
    }

    waitForPaymentConfirmation(line) {
        return new Promise((resolve) => {
            this.paymentLineResolvers[line.uuid] = resolve;
            this._startPolling(line);
        });
    }

    _startPolling(line) {
        let attempts = 0;
        const maxAttempts = 20;

        if (this.pollingHandles[line.uuid]) {
            clearInterval(this.pollingHandles[line.uuid]);
        }

        this.pollingHandles[line.uuid] = setInterval(async () => {
            attempts += 1;

            const finished = await this.handleNetpayStatusResponse(line);

            if (finished || attempts >= maxAttempts) {
                clearInterval(this.pollingHandles[line.uuid]);
                delete this.pollingHandles[line.uuid];

                if (!finished && attempts >= maxAttempts) {
                    line.setPaymentStatus("retry");
                    this._showError(_t("Netpay terminal timeout."));
                    const resolver = this.paymentLineResolvers?.[line.uuid];
                    if (resolver) {
                        resolver(false);
                        delete this.paymentLineResolvers[line.uuid];
                    }
                }
            }
        }, 3000);
    }

    async handleNetpayStatusResponse(line) {
        const notification = await this.pos.data
            .silentCall("pos.payment.method", "get_latest_netpay_status", [[this.payment_method_id.id]])
            .catch(this._handleOdooConnectionFailure.bind(this));

        if (!notification) {
            return false;
        }

        if (notification.folioNumber !== line.netpayFolioNumber) {
            return false;
        }

        const isSuccess = notification.responseCode === "00";

        if (isSuccess) {
            this.handleSuccessResponse(line, notification);
        } else {
            this._showError(notification.message || _t("Netpay payment failed."));
            line.setPaymentStatus("retry");
        }

        const resolver = this.paymentLineResolvers?.[line.uuid];
        if (resolver) {
            resolver(isSuccess);
            delete this.paymentLineResolvers[line.uuid];
        } else {
            line?.handlePaymentResponse(isSuccess);
        }

        return true;
    }

    handleSuccessResponse(line, notification) {
        line.setPaymentStatus("done");
        line.transaction_id = notification.orderId || "";
        line.card_type = notification.cardType || "";
        line.cardholder_name = notification.cardHolderName || "";
    }
}

register_payment_method("netpay", PaymentNetpay);
