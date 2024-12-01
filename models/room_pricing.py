from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class RoomPricingRule(models.Model):
    _name = 'hotel.pricing.rule'
    _description = 'Hotel Room Pricing Rule'

    # Basic Rule Information
    name = fields.Char(
        string='Rule Name', 
        required=True, 
        help='Descriptive name for the pricing rule'
    )
    active = fields.Boolean(
        string='Active', 
        default=True
    )

    # Pricing Rule Types
    rule_type = fields.Selection([
        ('seasonal', 'Seasonal Pricing'),
        ('weekday', 'Weekday/Weekend Pricing'),
        ('occupancy', 'Occupancy-Based Pricing'),
        ('lastminute', 'Last-Minute Discount'),
        ('advance', 'Advanced Booking Discount'),
        ('event', 'Special Event Pricing')
    ], string='Pricing Rule Type', 
      required=True
    )

    # Temporal Constraints
    start_date = fields.Date(
        string='Start Date', 
        required=True
    )
    end_date = fields.Date(
        string='End Date', 
        required=True
    )

    # Pricing Adjustment Mechanism
    adjustment_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ('multiplier', 'Multiplier')
    ], string='Adjustment Type', 
      required=True
    )
    adjustment_value = fields.Float(
        string='Adjustment Value', 
        required=True
    )

    # Applicability
    room_type_ids = fields.Many2many(
        'hotel.room.type', 
        string='Applicable Room Types'
    )
    
    # Advanced Conditions
    min_stay_duration = fields.Integer(
        string='Minimum Stay Duration', 
        default=0
    )
    max_occupancy = fields.Integer(
        string='Maximum Occupancy', 
        default=0
    )
    weekday_filter = fields.Selection([
        ('weekdays', 'Weekdays Only'),
        ('weekends', 'Weekends Only'),
        ('all', 'All Days')
    ], string='Day Type', 
      default='all'
    )

    @api.constrains('start_date', 'end_date')
    def _validate_date_range(self):
        """Validate that end date is after start date"""
        for record in self:
            if record.end_date < record.start_date:
                raise ValidationError("End date must be after start date")

    @api.model
    def calculate_dynamic_price(self, base_price, booking_date, room_type, stay_details):
        """
        Calculate dynamic price based on multiple pricing rules
        
        :param base_price: Original room price
        :param booking_date: Date of booking
        :param room_type: Room type being booked
        :param stay_details: Dictionary with stay information
        :return: Adjusted price
        """
        applicable_rules = self._find_applicable_rules(
            booking_date, room_type, stay_details
        )
        
        for rule in applicable_rules:
            base_price = rule._apply_rule(base_price, stay_details)
        
        return base_price

    def _find_applicable_rules(self, booking_date, room_type, stay_details):
        """Find all applicable pricing rules"""
        domain = [
            ('active', '=', True),
            ('start_date', '<=', booking_date),
            ('end_date', '>=', booking_date),
            ('room_type_ids', 'in', room_type.id)
        ]
        
        # Additional filtering based on rule types
        applicable_rules = self.search(domain)
        return applicable_rules.filtered(
            lambda r: r._rule_conditions_met(stay_details)
        )

    def _rule_conditions_met(self, stay_details):
        """Check if specific rule conditions are satisfied"""
        self.ensure_one()
        
        # Weekday/Weekend check
        if self.weekday_filter != 'all':
            is_weekend = stay_details.get('is_weekend', False)
            if (self.weekday_filter == 'weekdays' and is_weekend) or \
               (self.weekday_filter == 'weekends' and not is_weekend):
                return False
        
        # Minimum stay duration
        if self.min_stay_duration > 0 and \
           stay_details.get('stay_duration', 0) < self.min_stay_duration:
            return False
        
        # Maximum occupancy
        if self.max_occupancy > 0 and \
           stay_details.get('occupancy', 0) > self.max_occupancy:
            return False
        
        return True

    def _apply_rule(self, base_price, stay_details):
        """Apply pricing rule adjustment"""
        self.ensure_one()
        
        if self.adjustment_type == 'fixed':
            return base_price + self.adjustment_value
        elif self.adjustment_type == 'percentage':
            return base_price * (1 + (self.adjustment_value / 100))
        elif self.adjustment_type == 'multiplier':
            return base_price * self.adjustment_value
        
        return base_price