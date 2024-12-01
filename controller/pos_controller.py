from odoo import http
from odoo.http import request

class HotelPOSController(http.Controller):
    @http.route('/hotel/pos/services', type='json', auth='user')
    def get_pos_services(self):
        """Retrieve available POS services and products"""
        services = request.env['hotel.pos'].get_service_points()
        products = request.env['hotel.product'].search_read(
            [('available_in_pos', '=', True)], 
            ['name', 'list_price', 'service_point']
        )
        
        return {
            'services': services,
            'products': products
        }
    
    @http.route('/hotel/pos/order', type='json', auth='user', methods=['POST'])
    def create_pos_order(self, **kwargs):
        """Create POS order from web interface"""
        try:
            pos_order = request.env['hotel.pos'].create({
                'guest_id': kwargs.get('guest_id'),
                'service_point': kwargs.get('service_point'),
                'payment_method': kwargs.get('payment_method'),
            })
            
            for line in kwargs.get('order_lines', []):
                request.env['hotel.pos.line'].create({
                    'pos_id': pos_order.id,
                    'product_id': line['product_id'],
                    'quantity': line['quantity'],
                })
            
            return {'status': 'success', 'order_id': pos_order.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}