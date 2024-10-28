from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

db = SQLAlchemy()
Base = declarative_base()


# Utility functions for formatting
def format_datetime(value):
    return value.strftime('%Y-%m-%d %H:%M:%S') if value else None

def currency_conversions(opportunity):
    return {
        'usd': opportunity.usd,
        'aus': opportunity.aus,
        'cad': opportunity.cad
    }


# Define the Account model
class Account(db.Model):
    __tablename__ = 'account'
    account_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_name = db.Column(db.String(255), nullable=False)

    def account_to_dict(self):
        return {
            'account_id': self.account_id,
            'account_name': self.account_name
        }

# Define the Dealer model
class Dealer(db.Model):
    __tablename__ = 'dealer'
    dealer_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dealer_code = db.Column(db.String(50), nullable=False)
    opportunity_owner = db.Column(db.String(255), nullable=False)

    def dealer_to_dict(self):
        return {
            'dealer_id': self.dealer_id,
            'dealer_code': self.dealer_code,
            'opportunity_owner': self.opportunity_owner
        }

# Define the Opportunity model
class Opportunity(db.Model):
    __tablename__ = 'opportunity'
    opportunity_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_name = db.Column(db.String(255))
    account_id = db.Column(db.String, db.ForeignKey('account.account_id'))
    account = db.relationship('Account', backref='opportunities')
    close_date = db.Column(db.Date)
    amount = db.Column(db.DECIMAL(10, 2))
    description = db.Column(db.Text)
    dealer_id = db.Column(db.String, db.ForeignKey('dealer.dealer_id'))
    dealer_code = db.Column(db.String(50))
    dealer_name_or_opportunity_owner = db.Column(db.String(255))
    stage = db.Column(db.String(50))
    probability = db.Column(db.Integer)
    next_step = db.Column(db.String(255))
    created_date = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    amount_in_words = db.Column(db.String)
    usd = db.Column(db.Float)  # US Dollars
    aus = db.Column(db.Float)  # Australian Dollars
    cad = db.Column(db.Float)  # Canadian Dollars

    def opportunity_to_dict(self):
        return {
            'opportunity_id': self.opportunity_id,
            'opportunity_name': self.opportunity_name,
            'account_id': self.account_id,
            'account_name': self.account.account_name if self.account else None,
            'close_date': format_datetime(self.close_date),
            'amount': self.amount,
            'description': self.description,
            'dealer_id': self.dealer_id,
            'dealer_code': self.dealer_code,
            'dealer_name_or_opportunity_owner': self.dealer_name_or_opportunity_owner,
            'stage': self.stage,
            'probability': self.probability,
            'next_step': self.next_step,
            'created_date': format_datetime(self.created_date),
            'amount_in_words': self.amount_in_words,
            'currency_conversions': currency_conversions(self)
        }