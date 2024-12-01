from odoo import models, fields, api

class MembershipEnrollmentWizard(models.TransientModel):
    _name = 'hotel.membership.enrollment.wizard'
    _description = 'Membership Enrollment Wizard'

    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Guest', 
        required=True
    )
    
    initial_tier = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Initial Membership Tier', 
      default='bronze', 
      required=True
    )
    
    initial_points = fields.Float(
        string='Initial Points', 
        default=0.0
    )
    
    family_members = fields.One2many(
        'hotel.membership.enrollment.family', 
        'wizard_id', 
        string='Family Members'
    )

    def enroll_membership(self):
        """Create new membership for guest"""
        membership = self.env['hotel.membership'].create({
            'guest_id': self.guest_id.id,
            'tier': self.initial_tier,
            'points_balance': self.initial_points
        })
        
        # Add family members
        for family_line in self.family_members:
            self.env['hotel.membership.family'].create({
                'membership_id': membership.id,
                'guest_id': family_line.guest_id.id,
                'relationship': family_line.relationship
            })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.membership',
            'res_id': membership.id,
            'view_mode': 'form',
        }


class MembershipEnrollmentFamilyWizard(models.TransientModel):
    _name = 'hotel.membership.enrollment.family'
    _description = 'Membership Enrollment Family Members'
    
    wizard_id = fields.Many2one(
        'hotel.membership.enrollment.wizard', 
        string='Enrollment Wizard', 
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