from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import re

class GuestProfile(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'full_name'

    # Personal Information
    first_name = fields.Char(
        string='First Name', 
        required=True, 
        tracking=True
    )
    last_name = fields.Char(
        string='Last Name', 
        required=True, 
        tracking=True
    )
    full_name = fields.Char(
        string='Full Name', 
        compute='_compute_full_name', 
        store=True
    )
    
    # Contact Details
    email = fields.Char(
        string='Email', 
        required=True, 
        tracking=True
    )
    phone = fields.Char(
        string='Phone Number', 
        tracking=True
    )
    
    # Identification
    passport_number = fields.Char(
        string='Passport Number', 
        tracking=True
    )
    national_id = fields.Char(
        string='National ID', 
        tracking=True
    )
    
    # Personal Details
    birthdate = fields.Date(
        string='Date of Birth', 
        tracking=True
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say')
    ], string='Gender', tracking=True)
    
    # Stay History
    booking_ids = fields.One2many(
        'hotel.booking', 
        'guest_id', 
        string='Booking History'
    )
    total_stays = fields.Integer(
        string='Total Stays', 
        compute='_compute_stay_statistics'
    )
    total_nights = fields.Integer(
        string='Total Nights', 
        compute='_compute_stay_statistics'
    )
    
    # Preferences
    preferred_room_type = fields.Many2one(
        'hotel.room.type', 
        string='Preferred Room Type'
    )
    dietary_preferences = fields.Text(
        string='Dietary Preferences'
    )
    special_requests = fields.Text(
        string='Special Requests'
    )
    
    # Loyalty Program
    loyalty_member = fields.Boolean(
        string='Loyalty Member', 
        default=False
    )
    loyalty_tier = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Loyalty Tier', tracking=True)
    loyalty_points = fields.Float(
        string='Loyalty Points', 
        default=0.0
    )
    
    # Communication Preferences
    newsletter_subscription = fields.Boolean(
        string='Newsletter Subscription', 
        default=True
    )
    communication_channel = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('post', 'Postal Mail')
    ], string='Preferred Communication Channel')
    
    # Compliance and Privacy
    privacy_consent = fields.Boolean(
        string='Privacy Consent', 
        required=True
    )
    last_communication_date = fields.Datetime(
        string='Last Communication', 
        tracking=True
    )

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        """Compute full name from first and last names"""
        for record in self:
            record.full_name = f"{record.first_name} {record.last_name}".strip()

    @api.constrains('email')
    def _validate_email(self):
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_regex, record.email):
                raise ValidationError("Invalid email format")

    @api.constrains('birthdate')
    def _validate_birthdate(self):
        """Ensure birthdate is not in the future"""
        for record in self:
            if record.birthdate and record.birthdate > date.today():
                raise ValidationError("Birthdate cannot be in the future")

    @api.depends('booking_ids')
    def _compute_stay_statistics(self):
        """Compute total stays and nights"""
        for record in self:
            record.total_stays = len(record.booking_ids)
            record.total_nights = sum(
                booking.nights for booking in record.booking_ids
            )

    def update_loyalty_tier(self):
        """Automatically update loyalty tier based on points"""
        for record in self:
            if record.loyalty_points < 500:
                record.loyalty_tier = 'bronze'
            elif record.loyalty_points < 2000:
                record.loyalty_tier = 'silver'
            elif record.loyalty_points < 5000:
                record.loyalty_tier = 'gold'
            else:
                record.loyalty_tier = 'platinum'

    def send_personalized_communication(self, message_type):
        """Send personalized communication based on preferences"""
        self.ensure_one()
        if not self.privacy_consent:
            return False

        communication_methods = {
            'welcome': self._send_welcome_message,
            'birthday': self._send_birthday_greeting,
            'stay_reminder': self._send_stay_reminder
        }

        method = communication_methods.get(message_type)
        if method:
            return method()
        return False

    def _send_welcome_message(self):
        """Send a personalized welcome message"""
        # Implementation would depend on communication channel
        # Placeholder for actual communication logic
        self.last_communication_date = fields.Datetime.now()
        return True

    def _send_birthday_greeting(self):
        """Send birthday greeting if it's guest's birthday"""
        # Placeholder for birthday greeting logic
        self.last_communication_date = fields.Datetime.now()
        return True

    def _send_stay_reminder(self):
        """Send stay reminder or follow-up"""
        # Placeholder for stay reminder logic
        self.last_communication_date = fields.Datetime.now()
        return True

    def award_loyalty_points(self, points):
        """Award loyalty points and update tier"""
        self.ensure_one()
        self.loyalty_points += points
        self.update_loyalty_tier()

