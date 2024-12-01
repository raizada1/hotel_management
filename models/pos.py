from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HotelPointOfSale(models.Model):
    _name = 'hotel.pos'
    _description = 'Hotel Point of Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Order Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hotel.pos')
    )
    
    service_point = fields.Selection([
        ('restaurant', 'Restaurant'),
        ('bar', 'Bar'),
        ('spa', 'Spa'),
        ('gift_shop', 'Gift Shop'),
        ('room_service', 'Room Service'),
        ('other', 'Other Services')
    ], string='Service Point', required=True)
    
    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Guest', 
        required=True,
        tracking=True
    )
    
    room_id = fields.Many2one(
        'hotel.room', 
        string='Guest Room', 
        related='guest_id.room_id', 
        readonly=True
    )
    
    order_lines = fields.One2many(
        'hotel.pos.line', 
        'pos_id', 
        string='Order Lines', 
        required=True
    )
    
    total_amount = fields.Monetary(
        string='Total Amount', 
        compute='_compute_total_amount', 
        store=True
    )
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        default=lambda self: self.env.company.currency_id
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    
    payment_method = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('membership', 'Membership Points')
    ], string='Payment Method')
    
    @api.depends('order_lines.subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.order_lines.mapped('subtotal'))
    
    def action_confirm(self):
        """Confirm the order and update inventory"""
        for order in self:
            order.state = 'confirmed'
            order._update_inventory()
    
    def action_pay(self):
        """Process payment and update guest billing"""
        for order in self:
            if order.state != 'confirmed':
                raise ValidationError("Order must be confirmed before payment")
            
            # Integrate with guest billing
            if order.payment_method == 'room_charge':
                order.guest_id.add_charge(order.total_amount)
            
            order.state = 'paid'
    
    def action_cancel(self):
        """Cancel the order and restore inventory"""
        for order in self:
            order.state = 'cancelled'
            order._restore_inventory()
    
    def _update_inventory(self):
        """Reduce inventory based on order items"""
        for line in self.order_lines:
            line.product_id.update_stock_quantity(-line.quantity)
    
    def _restore_inventory(self):
        """Restore inventory for cancelled orders"""
        for line in self.order_lines:
            line.product_id.update_stock_quantity(line.quantity)


class HotelPointOfSaleLine(models.Model):
    _name = 'hotel.pos.line'
    _description = 'POS Order Line'
    
    pos_id = fields.Many2one(
        'hotel.pos', 
        string='POS Order', 
        required=True, 
        ondelete='cascade'
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
    
    unit_price = fields.Monetary(
        related='product_id.list_price', 
        string='Unit Price', 
        readonly=True
    )
    
    subtotal = fields.Monetary(
        string='Subtotal', 
        compute='_compute_subtotal', 
        store=True
    )
    
    tax_ids = fields.Many2many(
        'account.tax', 
        string='Taxes'
    )
    
    @api.depends('quantity', 'unit_price', 'tax_ids')
    def _compute_subtotal(self):
        for line in self:
            base_subtotal = line.quantity * line.unit_price
            taxes = line.tax_ids.compute_all(base_subtotal)
            line.subtotal = taxes['total_included']