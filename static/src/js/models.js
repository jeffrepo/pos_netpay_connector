odoo.define('pos_netpay_connector.models', function(require) {
    'use strict';

    const models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    // var models = require('point_of_sale.models');
    const rpc = require('web.rpc');
    var { Gui } = require('point_of_sale.Gui');

    
//     var posmodel_super = models.PosModel.prototype;
//     models.PosModel = models.PosModel.extend({



//         get_sale_netypay: async function(orders) {
//             console.log('orders 1')
//             console.log(orders)
//             console.log('')
//             console.log('')
//             return await this.rpc({
//                 model: 'pos.order',
//                 method: 'sale_netpay_ui',
//                 args: [[], [orders[0]]],
//             });
//         },


//         sending_values_netpay: async function(dicc){
//             return await this.rpc({
//                 model: 'pos.order',
//                 method: 'value_fields',
//                 args: [[], [dicc]],
//             });
//         },
        
        
//         sending_values_netpay: async function(dicc){
//             return await this.rpc({
//                 model: 'pos.order',
//                 method: 'value_fields',
//                 args: [[], [dicc]],
//             });
//         },
        
//         _save_to_server: async function(orders, options) {

//           var self = this;
//           var order = self.env.pos.get_order();
//           console.log('_save_to_server1');

//           if (orders.length){
//              console.log('1')
//              var sale_netypay = await this.get_sale_netypay(orders);
//              console.log(sale_netypay)
//              console.log('Consulta netpay')
//              if (sale_netypay['error'] != false){


//                   Gui.showPopup('ErrorPopup', {
//                       title: 'Error',
//                       body: sale_netypay['error'],
//                   });
//               }else{
//                   console.log('No hay error netpay');
//                   console.log(orders)
//                   console.log(order)
//                   console.log('')

//                   var server_id = await posmodel_super._save_to_server.apply(this, arguments);

//                   console.log('server_id')
//                   console.log(server_id)
//                   if(server_id.length){
//                       console.log('transaccion_exitosa')
//                       // errt['id_order']=server_id[0]['id']
//                       // var errt = await this.sending_values_red_mas(errt);
//                   }

//                   return server_id;
//               }
//           }else{
//               return await posmodel_super._save_to_server.apply(this, arguments);
//           }


//         }

//     });
    
    
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        
        initialize: function() {
            _super_order.initialize.apply(this,arguments);
            this.set_netpay_orderId();
        },
        
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            
            json.netpay_orderId = this.get_netpay_orderId();
            
            return json;
        },
        
        get_netpay_orderId: function(){
            return this.get('netpay_orderId');
        },
        
        set_netpay_orderId: function(netpay_orderId){
            this.set({
              netpay_orderId: netpay_orderId
            });
        },
        
    });

});
