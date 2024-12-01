
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Hotel Room Type'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(string='Room Type Name', required=True, translate=True)
    code = fields.Char(string='Room Type Code', required=True, copy=False)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    # Capacity and Occupancy
    max_adults = fields.Integer(string='Max Adults', required=True, default=2)
    max_children = fields.Integer(string='Max Children', required=True, default=1)
    
    # Pricing
    base_price = fields.Float(string='Base Price', required=True, help='Standard rate for this room type')
    
    # Descriptive Fields
    description = fields.Text(string='Description', translate=True)
    room_size = fields.Float(string='Room Size (sq. m)', help='Total room area')
    
    # View Type Selection
    view_type = fields.Selection([
        ('standard', 'Standard View'),
        ('city', 'City View'),
        ('ocean', 'Ocean View'),
        ('mountain', 'Mountain View'),
        ('garden', 'Garden View'),
        ('pool', 'Pool View')
    ], string='View Type', default='standard')
    
    # Amenities
    amenities = fields.Many2many(
        'hotel.room.amenity', 
        string='Standard Amenities',
        help='Standard amenities included in this room type'
    )
    
    # Computed Fields
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.code})"
    
    # Constraints and Validations
    @api.constrains('max_adults', 'max_children')
    def _check_occupancy_limits(self):
        for record in self:
            if record.max_adults < 1:
                raise ValidationError("Minimum 1 adult must be allowed in a room type.")
            if record.max_children < 0:
                raise ValidationError("Children count cannot be negative.")
            if record.max_adults + record.max_children > 6:
                raise ValidationError("Maximum total occupancy cannot exceed 6 persons.")
    
    @api.constrains('base_price')
    def _check_base_price(self):
        for record in self:
            if record.base_price <= 0:
                raise ValidationError("Room type base price must be positive.")
    
    # SQL Constraints
    _sql_constraints = [
        ('unique_room_type_code', 'unique(code)', 'Room type code must be unique!'),
    ]
    
    # Methods
    def action_view_rooms(self):
        """
        Action to view all rooms of this type
        """
        return {
            'type': 'ir.actions.act_window',
            'name': f'Rooms - {self.name}',
            'res_model': 'hotel.room',
            'view_mode': 'tree,form',
            'domain': [('room_type_id', '=', self.id)],
            'context': {
                'default_room_type_id': self.id,
            }
        }