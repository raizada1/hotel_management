from odoo import models, fields, api

class POSOrderWizard(models.TransientModel):
    _name = 'hotel.pos.wizard'
    _description = 'POS Order Creation Wizard'

    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Guest', 
        required=True
    )
    
    service_point = fields.Selection([
        ('restaurant', 'Restaurant'),
        ('bar', 'Bar'),
        ('spa', 'Spa'),
        ('gift_shop', 'Gift Shop'),
        ('room_service', 'Room Service'),
        ('other', 'Other Services')
    ], string='Service Point', required=True)
    
    product_lines = fields.One2many(
        'hotel.pos.wizard.line', 
        'wizard_id', 
        string='Products'
    )
    
    payment_method = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('membership', 'Membership Points')
    ], string='Payment Method', required=True)
    
    def create_pos_order(self):
        """Create POS order from wizard"""
        pos_order = self.env['hotel.pos'].create({
            'guest_id': self.guest_id.id,
            'service_point': self.service_point,
            'payment_method': self.payment_method,
        })
        
        for line in self.product_lines:
            self.env['hotel.pos.line'].create({
                'pos_id': pos_order.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.pos',
            'res_id': pos_order.id,
            'view_mode': 'form',
        }


class POSOrderWizardLine(models.TransientModel):
    _name = 'hotel.pos.wizard.line'
    _description = 'POS Order Wizard Line'
    
    wizard_id = fields.Many2one(
        'hotel.pos.wizard', 
        string='Wizard', 
        required=True
    )
    
    product_id = fields.Many2one(
        'hotel.product', 
        string='Product', 
        required=True
    )
    
    quantity = fields.Float(
        string='Quantity', 
        default=1.0, 
        required=True
    )