from odoo import models, fields, api
from odoo.exceptions import ValidationError
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import logging

_logger = logging.getLogger(__name__)

class HotelAnalytics(models.Model):
    _name = 'hotel.analytics'
    _description = 'Advanced Hotel Performance Analytics'

    # Core Analytics Attributes
    name = fields.Char(string='Analysis Name', required=True)
    analysis_type = fields.Selection([
        ('occupancy', 'Occupancy Analysis'),
        ('revenue', 'Revenue Prediction'),
        ('guest_segmentation', 'Guest Segmentation'),
        ('performance', 'Overall Performance')
    ], string='Analysis Type', required=True)

    # Analysis Parameters
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    # Predictive Insights
    occupancy_forecast = fields.Float(
        string='Occupancy Forecast (%)', 
        compute='_compute_occupancy_forecast'
    )
    revenue_prediction = fields.Monetary(
        string='Revenue Prediction', 
        compute='_compute_revenue_prediction'
    )

    # Visualization Storage
    visualization_image = fields.Binary(string='Analysis Visualization')

    # Guest Segmentation Results
    guest_segments = fields.Text(string='Guest Segments')

    @api.model
    def create_occupancy_forecast(self, date_from, date_to):
        """
        Generate occupancy forecast using machine learning
        """
        try:
            # Retrieve historical booking data
            bookings = self.env['hotel.booking'].search([
                ('create_date', '>=', date_from),
                ('create_date', '<=', date_to)
            ])

            # Prepare data for ML model
            data = pd.DataFrame([{
                'bookings': len(bookings),
                'month': booking.create_date.month,
                'day_of_week': booking.create_date.weekday(),
                'is_weekend': booking.create_date.weekday() in [5, 6]
            } for booking in bookings])

            # Train Random Forest Regressor
            X = data.drop('bookings', axis=1)
            y = data['bookings']
            
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)

            # Predict future occupancy
            future_data = pd.DataFrame({
                'month': [date_from.month],
                'day_of_week': [date_from.weekday()],
                'is_weekend': [date_from.weekday() in [5, 6]]
            })

            forecast = model.predict(future_data)[0]
            
            return forecast
        except Exception as e:
            _logger.error(f"Occupancy forecast error: {str(e)}")
            return 0

    def _compute_occupancy_forecast(self):
        """
        Compute occupancy forecast for each record
        """
        for record in self:
            record.occupancy_forecast = self.create_occupancy_forecast(
                record.date_from, 
                record.date_to
            )

    def create_guest_segmentation(self):
        """
        Perform advanced guest segmentation using K-means clustering
        """
        try:
            # Retrieve guest data
            guests = self.env['hotel.guest'].search([])
            
            # Prepare features for segmentation
            data = pd.DataFrame([{
                'total_stays': guest.total_stays,
                'avg_spend': guest.total_revenue / max(guest.total_stays, 1),
                'loyalty_points': guest.loyalty_points
            } for guest in guests])

            # Normalize data
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)

            # Perform K-means clustering
            kmeans = KMeans(n_clusters=4, random_state=42)
            data['cluster'] = kmeans.fit_predict(scaled_data)

            # Analyze clusters
            segments = data.groupby('cluster').agg({
                'total_stays': 'mean',
                'avg_spend': 'mean',
                'loyalty_points': 'mean'
            }).to_dict('index')

            return segments
        except Exception as e:
            _logger.error(f"Guest segmentation error: {str(e)}")
            return {}

    def _compute_revenue_prediction(self):
        """
        Predictive revenue modeling
        """
        for record in self:
            try:
                # Retrieve historical revenue data
                bookings = self.env['hotel.booking'].search([
                    ('create_date', '>=', record.date_from),
                    ('create_date', '<=', record.date_to)
                ])

                total_revenue = sum(booking.total_price for booking in bookings)
                
                # Simple predictive model using moving average
                record.revenue_prediction = total_revenue * 1.1  # 10% growth prediction
            except Exception as e:
                _logger.error(f"Revenue prediction error: {str(e)}")
                record.revenue_prediction = 0

    def generate_performance_visualization(self):
        """
        Create comprehensive performance visualization
        """
        try:
            # Retrieve performance data
            bookings = self.env['hotel.booking'].search([])
            
            # Create DataFrame
            data = pd.DataFrame([{
                'month': booking.create_date.month,
                'revenue': booking.total_price,
                'occupancy': 1 if booking.state == 'confirmed' else 0
            } for booking in bookings])

            # Monthly aggregation
            monthly_data = data.groupby('month').agg({
                'revenue': 'sum',
                'occupancy': 'mean'
            }).reset_index()

            # Create visualization
            plt.figure(figsize=(10, 6))
            plt.subplot(2, 1, 1)
            plt.bar(monthly_data['month'], monthly_data['revenue'])
            plt.title('Monthly Revenue')
            plt.xlabel('Month')
            plt.ylabel('Revenue')

            plt.subplot(2, 1, 2)
            plt.plot(monthly_data['month'], monthly_data['occupancy'], marker='o')
            plt.title('Monthly Occupancy Rate')
            plt.xlabel('Month')
            plt.ylabel('Occupancy Rate')

            plt.tight_layout()

            # Save plot to binary
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue())
        except Exception as e:
            _logger.error(f"Visualization generation error: {str(e)}")
            return False