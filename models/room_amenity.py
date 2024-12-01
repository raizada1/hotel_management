
from odoo import models, fields, api

class RoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Hotel Room Amenity'

    name = fields.Char(string='Amenity Name', required=True, translate=True)
    icon = fields.Char(string='Icon', help='Icon representing the amenity')
    description = fields.Text(string='Description', translate=True)
    
    # Optional: Add a boolean to indicate if it's a standard amenity
    is_standard = fields.Boolean(string='Standard Amenity', default=False)

    # Constraint to ensure unique amenity names
    _sql_constraints = [
        ('unique_amenity_name', 'unique(name)', 'Amenity name must be unique!')
    ]

    def name_get(self):
        """Custom name get method to display amenities with icons"""
        result = []
        for amenity in self:
            name = f"{amenity.icon or ''} {amenity.name}".strip()
            result.append((amenity.id, name))
        return result