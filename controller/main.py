
from odoo import http
from odoo.http import request

class HotelManagementController(http.Controller):
    @http.route('/hotel/room-types', type='json', auth='public', methods=['GET'])
    def get_room_types(self):
        """
        Retrieve available room types for web display
        """
        room_types = request.env['hotel.room.type'].sudo().search_read(
            [],
            ['name', 'code', 'base_price', 'max_adults', 'max_children', 'description']
        )
        return room_types

    @http.route('/hotel/check-availability', type='json', auth='public', methods=['POST'])
    def check_room_availability(self, **kwargs):
        """
        Check room availability for given dates
        """
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        room_type_id = kwargs.get('room_type_id')

        # Implement availability checking logic
        available_rooms = request.env['hotel.room'].sudo().search([
            ('room_type_id', '=', room_type_id),
            ('state', '=', 'available')
        ])

        return {
            'available_rooms_count': len(available_rooms),
            'available_rooms': available_rooms.mapped('name')
        }