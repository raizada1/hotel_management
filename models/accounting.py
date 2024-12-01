from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HotelAccounting(models.Model):
    _name = 'hotel.accounting'
    _description = 'Comprehensive Hotel Accounting Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Enhanced Transaction Tracking
    name = fields.Char(
        string='Transaction Reference', 
        required=True, 
        copy=False, 
        index=True,
        track_visibility='onchange'
    )
    
    transaction_type = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('service', 'Service Transaction'),
        ('membership', 'Membership Fee'),
        ('refund', 'Refund'),
        ('advance_payment', 'Advance Payment'),
        ('penalty', 'Penalty Charge')
    ], string='Transaction Type', required=True)

    # Advanced Financial Tracking
    guest_id = fields.Many2one(
        'hotel.guest', 
        string='Guest', 
        required=True,
        track_visibility='always'
    )
    booking_id = fields.Many2one(
        'hotel.booking', 
        string='Related Booking',
        tracking=True
    )
    
    # Comprehensive Financial Attributes
    total_amount = fields.Monetary(
        string='Total Amount', 
        currency_field='currency_id',
        tracking=True
    )
    tax_amount = fields.Monetary(
        string='Tax Amount', 
        currency_field='currency_id',
        compute='_compute_tax_details',
        store=True
    )
    net_amount = fields.Monetary(
        string='Net Amount', 
        currency_field='currency_id', 
        compute='_compute_net_amount',
        store=True
    )
    
    # Enhanced Payment Status
    payment_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Payment'),
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('refunded', 'Refunded')
    ], default='draft', tracking=True)

    # Advanced Currency and Taxation
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        default=lambda self: self.env.company.currency_id
    )
    tax_rate = fields.Float(
        string='Tax Rate (%)', 
        default=18.0,  # Standard GST rate
        tracking=True
    )
    
    # Enhanced Revenue Categorization
    revenue_category = fields.Selection([
        ('room_revenue', 'Room Revenue'),
        ('food_beverage', 'Food & Beverage'),
        ('spa', 'Spa Services'),
        ('conference', 'Conference Services'),
        ('retail', 'Retail Sales'),
        ('other', 'Other Services')
    ], string='Revenue Category', tracking=True)

    # Payment Details
    payment_date = fields.Date(string='Payment Date')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment')
    ], string='Payment Method')

    # Compute Methods with Enhanced Logic
    @api.depends('total_amount', 'tax_rate')
    def _compute_tax_details(self):
        for record in self:
            record.tax_amount = record.total_amount * (record.tax_rate / 100)

    @api.depends('total_amount', 'tax_amount')
    def _compute_net_amount(self):
        for record in self:
            record.net_amount = record.total_amount - record.tax_amount

    # Advanced Business Logic Methods
    @api.model
    def create(self, vals):
        # Generate unique transaction reference
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.accounting') or '/'
        
        self._validate_transaction(vals)
        return super(HotelAccounting, self).create(vals)

    def _validate_transaction(self, vals):
        # Comprehensive transaction validation
        if 'total_amount' in vals and vals['total_amount'] < 0:
            raise ValidationError("Transaction amount cannot be negative.")
        
        # Advanced tax calculation
        if 'total_amount' in vals and 'tax_rate' in vals:
            vals['tax_amount'] = vals['total_amount'] * (vals['tax_rate'] / 100)

    # Advanced Reporting Method
    def generate_financial_report(self, date_from, date_to):
        """
        Generate comprehensive financial report with advanced analytics
        """
        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to)
        ]
        
        report = {
            'total_revenue': 0,
            'total_tax': 0,
            'transaction_count': 0,
            'transaction_breakdown': {},
            'payment_status_summary': {}
        }
        
        transactions = self.search(domain)
        
        for transaction in transactions:
            report['total_revenue'] += transaction.total_amount
            report['total_tax'] += transaction.tax_amount
            report['transaction_count'] += 1
            
            # Revenue categorization
            category = transaction.revenue_category
            report['transaction_breakdown'][category] = report['transaction_breakdown'].get(category, 0) + transaction.total_amount
            
            # Payment status tracking
            status = transaction.payment_status
            report['payment_status_summary'][status] = report['payment_status_summary'].get(status, 0) + 1
        
        return report

    # Advanced Payment Reconciliation
    def reconcile_overdue_payments(self):
        """
        Automated overdue payment reconciliation
        """
        overdue_threshold = datetime.now() - timedelta(days=30)
        overdue_transactions = self.search([
            ('payment_status', 'in', ['pending', 'partial']),
            ('create_date', '<', overdue_threshold)
        ])
        
        for transaction in overdue_transactions:
            transaction.write({'payment_status': 'overdue'})
            # Log activity for management
            self.activity_schedule(
                'mail.mail_activity_data_warning', 
                user_id=self.env.user.id, 
                note=f'Overdue payment for transaction {transaction.name}'
            )

    def action_generate_invoice(self):
        """
        Generate detailed invoice for the transaction
        """
        self.ensure_one()
        try:
            # Logic to generate and potentially send invoice
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                # Additional invoice generation logic
            }
        except Exception as e:
            _logger.error(f"Invoice generation error: {str(e)}")
            raise UserError("Could not generate invoice. Please check system logs.")