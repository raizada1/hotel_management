from odoo import http
from odoo.http import request

class HotelMembershipController(http.Controller):
    @http.route('/hotel/membership/points', type='json', auth='user')
    def get_membership_points(self, guest_id):
        """Retrieve membership points for a guest"""
        membership = request.env['hotel.membership'].search([
            ('guest_id', '=', guest_id)
        ], limit=1)
        
        if not membership:
            return {
                'status': 'error',
                'message': 'No membership found for this guest'
            }
        
        return {
            'status': 'success',
            'points_balance': membership.points_balance,
            'tier': membership.tier,
            'total_points_earned': membership.total_points_earned
        }
    
    @http.route('/hotel/membership/redeem', type='json', auth='user', methods=['POST'])
    def redeem_membership_points(self, guest_id, points, description=None):
        """Redeem points for a guest membership"""
        try:
            membership = request.env['hotel.membership'].search([
                ('guest_id', '=', guest_id)
            ], limit=1)
            
            if not membership:
                return {
                    'status': 'error',
                    'message': 'No membership found for this guest'
                }
            
            membership.redeem_points(points, description)
            
            return {
                'status': 'success',
                'new_balance': membership.points_balance
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }