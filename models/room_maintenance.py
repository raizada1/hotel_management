from odoo import models, fields, api
from datetime import datetime, timedelta

class RoomMaintenance(models.Model):
    _name = 'hotel.room.maintenance'
    _description = 'Room Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Maintenance Request', 
        required=True, 
        tracking=True
    )
    
    room_id = fields.Many2one(
        'hotel.room', 
        string='Room', 
        required=True, 
        tracking=True
    )
    
    maintenance_type = fields.Selection([
        ('cleaning', 'Deep Cleaning'),
        ('repair', 'Repair'),
        ('renovation', 'Renovation'),
        ('inspection', 'Routine Inspection')
    ], string='Type', required=True, default='cleaning')
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    technician_id = fields.Many2one(
        'hr.employee', 
        string='Assigned Technician'
    )
    
    start_date = fields.Datetime(
        string='Start Date', 
        default=fields.Datetime.now
    )
    
    completion_date = fields.Datetime(string='Completion Date')
    
    description = fields.Text(string='Maintenance Details')
    
    cost = fields.Monetary(
        string='Maintenance Cost', 
        currency_field='company_currency_id'
    )
    
    company_currency_id = fields.Many2one(
        'res.currency', 
        related='company_id.currency_id'
    )
    
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.company
    )
    
    @api.model
    def create_routine_maintenance(self):
        """Create routine maintenance for rooms"""
        rooms = self.env['hotel.room'].search([
            ('last_maintenance_date', '<=', 
             datetime.now() - timedelta(days=90))
        ])
        
        for room in rooms:
            self.create({
                'name': f'Routine Maintenance - {room.name}',
                'room_id': room.id,
                'maintenance_type': 'inspection',
                'priority': 'medium',
                'state': 'scheduled'
            })
            
            room.last_maintenance_date = datetime.now()
    
    def action_start_maintenance(self):
        """Start maintenance process"""
        self.write({
            'state': 'in_progress', 
            'start_date': datetime.now()
        })
    
    def action_complete_maintenance(self):
        """Complete maintenance process"""
        self.write({
            'state': 'completed', 
            'completion_date': datetime.now()
        })
        
    def unlink(self):
        """Prevent deletion of completed maintenance records"""
        for record in self:
            if record.state == 'completed':
                raise models.ValidationError(
                    "Cannot delete completed maintenance records"
                )
        return super().unlink()