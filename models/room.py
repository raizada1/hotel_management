
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import generate_random_barcode

class Room(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _rec_name = 'display_name'
    
    # Room Identification
    name = fields.Char(
        string='Room Number', 
        required=True, 
        copy=False, 
        default=lambda self: self.env['ir.sequence'].next_by_code('hotel.room.sequence')
    )
    barcode = fields.Char(
        string='Room Barcode', 
        copy=False, 
        default=lambda self: generate_random_barcode()
    )
    display_name = fields.Char(
        string='Display Name', 
        compute='_compute_display_name', 
        store=True
    )
    
    # Room Type and Characteristics
    room_type_id = fields.Many2one(
        'hotel.room.type', 
        string='Room Type', 
        required=True
    )
    floor_number = fields.Integer(string='Floor Number', required=True)
    
    # Status and Availability
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('out_of_service', 'Out of Service')
    ], string='Room Status', default='draft')
    
    # Additional Room Details
    view_type = fields.Selection(
        related='room_type_id.view_type', 
        string='View Type', 
        store=True
    )
    current_price = fields.Float(
        string='Current Price', 
        compute='_compute_current_price', 
        store=True
    )
    
    # Computed Fields
    @api.depends('name', 'room_type_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} - {record.room_type_id.name}"
    
    @api.depends('room_type_id', 'state')
    def _compute_current_price(self):
        for record in self:
            # Base logic: use room type base price
            # In future, this can be enhanced with dynamic pricing
            record.current_price = record.room_type_id.base_price
    
    # Constraints and Validations
    @api.constrains('floor_number')
    def _check_floor_number(self):
        for record in self:
            if record.floor_number < 0:
                raise ValidationError("Floor number cannot be negative.")
    
    @api.constrains('name')
    def _check_unique_room_number(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name), 
                ('id', '!=', record.id)
            ])
            if duplicate:
                raise ValidationError(f"Room number {record.name} already exists.")
    
    # State Management Methods
    def action_mark_available(self):
        """Mark room as available"""
        self.write({'state': 'available'})
    
    def action_mark_maintenance(self):
        """Mark room for maintenance"""
        self.write({'state': 'maintenance'})
    
    def action_mark_cleaning(self):
        """Mark room for cleaning"""
        self.write({'state': 'cleaning'})
    
    # Reporting and Analytics
    def get_room_occupancy_rate(self, start_date, end_date):
        """
        Calculate room occupancy rate for a given period
        """
        # TODO: Implement occupancy calculation logic
        pass