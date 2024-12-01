from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = 'Hotel Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_in_date desc, id desc'

    # Basic Information
    name = fields.Char('Booking Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    
    # Guest Information
    partner_id = fields.Many2one('res.partner', string='Guest', required=True, tracking=True)
    email = fields.Char(related='partner_id.email', string='Email')
    phone = fields.Char(related='partner_id.phone', string='Phone')
    
    # Dates and Times
    check_in_date = fields.Date(string='Check-in Date', required=True, tracking=True)
    check_out_date = fields.Date(string='Check-out Date', required=True, tracking=True)
    expected_check_in_time = fields.Float(string='Expected Check-in Time')
    expected_check_out_time = fields.Float(string='Expected Check-out Time')
    actual_check_in = fields.Datetime(string='Actual Check-in', readonly=True)
    actual_check_out = fields.Datetime(string='Actual Check-out', readonly=True)
    duration_of_stay = fields.Integer(compute='_compute_duration_of_stay', 
                                    string='Duration of Stay (nights)', store=True)

    # Room Details
    room_id = fields.Many2one('hotel.room', string='Room', tracking=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', required=True)
    adults = fields.Integer(string='Adults', required=True, default=1)
    children = fields.Integer(string='Children', default=0)
    
    # Pricing
    currency_id = fields.Many2one('res.currency', 
                                 default=lambda self: self.env.company.currency_id)
    room_rate = fields.Monetary(string='Room Rate per Night')
    total_amount = fields.Monetary(compute='_compute_total_amount', store=True, 
                                 string='Total Amount')
    tax_amount = fields.Monetary(compute='_compute_tax_amount', store=True)
    deposit_amount = fields.Monetary(string='Deposit Amount')
    deposit_paid = fields.Boolean(string='Deposit Paid', default=False)
    
    # Status and State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    cancellation_reason = fields.Text(string='Cancellation Reason')
    cancellation_date = fields.Datetime(string='Cancellation Date')
    cancellation_fee = fields.Monetary(string='Cancellation Fee')
    
    # Additional Information
    special_requests = fields.Text(string='Special Requests', tracking=True)
    notes = fields.Text(string='Internal Notes')
    is_company = fields.Boolean(string='Is Company Booking')
    company_reference = fields.Char(string='Company Reference')
    
    # Payment Information
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid')
    ], string='Payment Status', default='unpaid', tracking=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.booking') or _('New')
        return super().create(vals_list)

    @api.depends('check_in_date', 'check_out_date')
    def _compute_duration_of_stay(self):
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                delta = booking.check_out_date - booking.check_in_date
                booking.duration_of_stay = delta.days
            else:
                booking.duration_of_stay = 0

    @api.depends('room_rate', 'duration_of_stay')
    def _compute_total_amount(self):
        for booking in self:
            booking.total_amount = booking.room_rate * booking.duration_of_stay

    @api.depends('total_amount')
    def _compute_tax_amount(self):
        # Assuming a default tax rate of 10%
        for booking in self:
            booking.tax_amount = booking.total_amount * 0.10

    @api.onchange('room_type_id')
    def _onchange_room_type(self):
        if self.room_type_id:
            self.room_rate = self.room_type_id.base_price
            # Reset room selection when room type changes
            self.room_id = False

    @api.constrains('check_in_date', 'check_out_date')
    def _check_dates(self):
        for booking in self:
            if booking.check_in_date and booking.check_out_date:
                if booking.check_in_date >= booking.check_out_date:
                    raise ValidationError(_("Check-out date must be after check-in date"))
                if booking.check_in_date < fields.Date.today():
                    raise ValidationError(_("Check-in date cannot be in the past"))

    @api.constrains('adults', 'children', 'room_type_id')
    def _check_occupancy(self):
        for booking in self:
            if booking.room_type_id:
                if booking.adults > booking.room_type_id.max_adults:
                    raise ValidationError(_("Number of adults exceeds room capacity"))
                if booking.children > booking.room_type_id.max_children:
                    raise ValidationError(_("Number of children exceeds room capacity"))

    def action_confirm(self):
        self.ensure_one()
        if not self.room_id:
            available_room = self._get_available_room()
            if not available_room:
                raise UserError(_("No available rooms of the selected type for the given dates"))
            self.room_id = available_room.id
        self.state = 'confirmed'
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['checked_in', 'checked_out', 'done']:
            raise UserError(_("Cannot cancel a booking that is already checked in or completed"))
        self.write({
            'state': 'cancelled',
            'cancellation_date': fields.Datetime.now()
        })
        return True

    def action_check_in(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed bookings can be checked in"))
        self.write({
            'state': 'checked_in',
            'actual_check_in': fields.Datetime.now()
        })
        # Update room status
        self.room_id.write({'state': 'occupied'})
        return True

    def action_check_out(self):
        self.ensure_one()
        if self.state != 'checked_in':
            raise UserError(_("Only checked-in bookings can be checked out"))
        self.write({
            'state': 'checked_out',
            'actual_check_out': fields.Datetime.now()
        })
        # Update room status and trigger cleaning
        self.room_id.write({'state': 'cleaning'})
        return True

    def _get_available_room(self):
        """Find an available room of the selected type for the booking dates"""
        domain = [
            ('room_type_id', '=', self.room_type_id.id),
            ('state', '=', 'available')
        ]
        # Check if room is not booked in the given date range
        conflicting_bookings = self.search([
            ('room_id', '!=', False),
            ('state', 'not in', ['cancelled', 'done']),
            ('check_in_date', '<', self.check_out_date),
            ('check_out_date', '>', self.check_in_date)
        ])
        unavailable_room_ids = conflicting_bookings.mapped('room_id').ids
        if unavailable_room_ids:
            domain.append(('id', 'not in', unavailable_room_ids))
        
        return self.env['hotel.room'].search(domain, limit=1)

    @api.model
    def _auto_cancel_expired_draft_bookings(self):
        """Automatically cancel draft bookings that are expired"""
        expiry_date = fields.Date.today() - timedelta(days=2)
        expired_bookings = self.search([
            ('state', '=', 'draft'),
            ('create_date', '<', expiry_date)
        ])
        expired_bookings.write({
            'state': 'cancelled',
            'cancellation_reason': 'Automatically cancelled - Expired draft booking',
            'cancellation_date': fields.Datetime.now()
        })

    def send_confirmation_email(self):
        """Send booking confirmation email to guest"""
        self.ensure_one()
        template = self.env.ref('hotel_management.booking_confirmation_email_template', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)