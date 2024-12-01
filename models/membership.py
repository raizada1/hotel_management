from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HotelMembership(models.Model):
    _name = 'hotel.membership'
    _description = 'Hotel Membership Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Membership Number', 
        required=True, 
        copy=False, 
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hotel.membership')
    )
    
    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Primary Member', 
        required=True,
        tracking=True
    )
    
    family_members = fields.One2many(
        'hotel.membership.family', 
        'membership_id', 
        string='Family Members'
    )
    
    tier = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Membership Tier', 
       default='bronze', 
       tracking=True
    )
    
    enrollment_date = fields.Date(
        string='Enrollment Date', 
        default=fields.Date.today,
        readonly=True
    )
    
    next_renewal_date = fields.Date(
        string='Next Renewal Date', 
        compute='_compute_renewal_date', 
        store=True
    )
    
    points_balance = fields.Float(
        string='Points Balance', 
        default=0.0,
        tracking=True
    )
    
    total_points_earned = fields.Float(
        string='Total Points Earned', 
        compute='_compute_total_points',
        store=True
    )
    
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended')
    ], string='Membership Status', 
      default='active', 
      tracking=True
    )
    
    benefit_ids = fields.Many2many(
        'hotel.membership.benefit', 
        string='Current Benefits'
    )
    
    @api.depends('enrollment_date')
    def _compute_renewal_date(self):
        for record in self:
            record.next_renewal_date = record.enrollment_date + relativedelta(years=1)
    
    @api.depends('points_balance')
    def _compute_total_points(self):
        for record in self:
            record.total_points_earned = record.points_balance
    
    def _update_tier(self):
        """Automatically update membership tier based on points"""
        tier_thresholds = {
            'bronze': 0,
            'silver': 1000,
            'gold': 5000,
            'platinum': 10000
        }
        
        for record in self:
            for tier, threshold in sorted(tier_thresholds.items(), key=lambda x: x[1]):
                if record.total_points_earned >= threshold:
                    record.tier = tier
    
    def add_points(self, points, description=False):
        """Add points to membership account"""
        for record in self:
            record.points_balance += points
            
            if description:
                self.env['hotel.membership.points.log'].create({
                    'membership_id': record.id,
                    'points': points,
                    'description': description
                })
            
            record._update_tier()
    
    def redeem_points(self, points, description=False):
        """Redeem points from membership account"""
        for record in self:
            if points > record.points_balance:
                raise ValidationError("Insufficient points balance")
            
            record.points_balance -= points
            
            if description:
                self.env['hotel.membership.points.log'].create({
                    'membership_id': record.id,
                    'points': -points,
                    'description': description
                })
    
    def renew_membership(self):
        """Renew membership and reset points if applicable"""
        for record in self:
            record.enrollment_date = fields.Date.today()
            record.next_renewal_date = record.enrollment_date + relativedelta(years=1)
            record.status = 'active'
            
            # Optional: Reset points based on tier
            tier_point_reset = {
                'bronze': 0,
                'silver': 500,
                'gold': 1000,
                'platinum': 2000
            }
            record.points_balance = tier_point_reset.get(record.tier, 0)


class HotelMembershipFamily(models.Model):
    _name = 'hotel.membership.family'
    _description = 'Membership Family Members'
    
    membership_id = fields.Many2one(
        'hotel.membership', 
        string='Membership', 
        required=True
    )
    
    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Family Member', 
        required=True
    )
    
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling')
    ], string='Relationship', required=True)


class HotelMembershipPointsLog(models.Model):
    _name = 'hotel.membership.points.log'
    _description = 'Membership Points Log'
    
    membership_id = fields.Many2one(
        'hotel.membership', 
        string='Membership', 
        required=True
    )
    
    date = fields.Datetime(
        string='Transaction Date', 
        default=fields.Datetime.now
    )
    
    points = fields.Float(string='Points')
    
    description = fields.Text(string='Description')


class HotelMembershipBenefit(models.Model):
    _name = 'hotel.membership.benefit'
    _description = 'Membership Benefits'
    
    name = fields.Char(string='Benefit Name', required=True)
    
    tier = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Available Tier', required=True)
    
    description = fields.Text(string='Benefit Description')
    
    point_cost = fields.Float(string='Point Cost')