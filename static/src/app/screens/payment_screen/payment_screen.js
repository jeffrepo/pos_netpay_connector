/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        console.log("PAYMENT_SCREEN.JS")
        console.log(this)
        onMounted(() => {
            const pendingPaymentLine = this.currentOrder.payment_ids.find(
                (paymentLine) =>
                    paymentLine.payment_method_id.use_payment_terminal === "netpay" &&
                    !paymentLine.isDone() &&
                    paymentLine.getPaymentStatus() !== "pending"
            );
            console.log(pendingPaymentLine)
            if (!pendingPaymentLine) {
                return;
            }

            // no-op por ahora; sirve para enganchar lógica de recuperación si la necesitas
        });
    },
});
