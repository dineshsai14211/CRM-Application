import random
import uuid
import os

from datetime import datetime

# thrid party imports
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import psycopg2

# local imports
from utilities.utility import get_probability, currency_conversion, convert_amount_to_word
from db_connection.configuration import DATABASE_URL
from db_table.tables import db, Account, Dealer, Opportunity
from log.log_switch import log_info, log_debug, log_error, log_warning

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

# Initialize SQLAlchemy with the Flask app
db.init_app(app)


@app.route("/", methods=["GET"])
def welcome():
    return jsonify({"message": "Welcome to the Backend Flask-CRM application", "status": "Success"}), 200

@app.route('/new_customer', methods=["POST"])
def register_new_customer():
    """
    Registers a new customer in the opportunity table.
    :return: JSON response with detailed customer information.
    """
    log_info("Registering a new customer")
    try:
        data = request.get_json()
        log_info(f"Received data: {data}")

        # Generate unique opportunity ID
        generated_opportunity_id = str(uuid.uuid1())
        created_timestamp = datetime.now()
        data.update({'created_date': created_timestamp, 'opportunity_id': generated_opportunity_id})

        # Validate account details
        customer_account_name = data.get("account_name")
        if not customer_account_name:
            log_error("account_name is required")
            return jsonify({"error": "account_name is required"}), 400

        # Check if the account exists
        existing_account = db.session.query(Account).filter_by(account_name=customer_account_name).first()
        if existing_account:
            account_id = existing_account.account_id
            log_info(f"Found existing account: {account_id}")
        else:
            # Create a new account if it doesn't exist
            account_id = str(uuid.uuid4())
            new_account = Account(account_id=account_id, account_name=customer_account_name)
            db.session.add(new_account)
            db.session.commit()
            log_info(f"Created new account: {account_id}")

        # Validate dealer details
        dealer_id = data.get("dealer_id")
        dealer_code = data.get("dealer_code")
        opportunity_name = data.get("opportunity_name")

        if not dealer_id or not dealer_code or not opportunity_name:
            log_error("dealer_id, dealer_code, and opportunity_name are required")
            return jsonify({"error": "dealer_id, dealer_code, and opportunity_name are required"}), 400

        # Check if the dealer exists
        existing_dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code
        ).first()

        if not existing_dealer:
            # Create a new dealer if it doesn't exist
            new_dealer = Dealer(dealer_id=dealer_id, dealer_code=dealer_code, opportunity_name=opportunity_name)
            db.session.add(new_dealer)
            db.session.commit()
            log_info(f"Created new dealer: {dealer_id}")

        # Parse close_date if provided
        close_date = data.get("close_date")
        if close_date:
            try:
                close_date = datetime.strptime(close_date, "%Y-%m-%d %H:%M:%S")
                log_info(f"Parsed close date: {close_date}")
            except ValueError as e:
                log_error(f"Invalid date format for close_date: {str(e)}")
                return jsonify({"error": f"Invalid date format for close_date: {str(e)}"}), 400
        else:
            close_date = None

        # Handle currency conversion
        opportunity_amount = data.get("amount")
        converted_currency_values = currency_conversion(opportunity_amount) if opportunity_amount else {}

        # Create a new opportunity record
        new_opportunity_record = Opportunity(
            opportunity_id=generated_opportunity_id,
            opportunity_name=opportunity_name,
            account_id=account_id,
            close_date=close_date,
            amount=opportunity_amount,
            description=data.get("description"),
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            stage=data.get("stage", "Unknown"),
            probability=data.get("probability"),
            next_step=data.get("next_step"),
            created_date=created_timestamp,
            usd=converted_currency_values.get("USD"),
            aus=converted_currency_values.get("AUD"),
            cad=converted_currency_values.get("CAD"),
            amount_in_words=convert_amount_to_word(opportunity_amount)
        )

        db.session.add(new_opportunity_record)
        db.session.commit()
        log_info(f"Created new opportunity: {generated_opportunity_id}")

        customer_data = new_opportunity_record.opportunity_to_dict()

        return jsonify({
            "message": "Customer created successfully",
            "customer_details": customer_data
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session in case of a database error
        log_error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        log_error(f"Internal server error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        db.session.close()

@app.route('/get-customers', methods=['GET'])
def get_all_customers():
    """
    Fetch all customers whose dealer code matches the given dealer code.
    """
    log_info("GET /get-customers - get_all_customers function has started")
    try:
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_name = request.args.get('opportunity_name')

        log_debug(f"GET /get-customers - dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_name={opportunity_name}")

        # Query the Dealer table for validation
        dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code
        ).first()

        if not dealer:
            log_debug(f"GET /get-customers - Invalid dealer information: dealer_id={dealer_id}, dealer_code={dealer_code}")
            return jsonify({"error": "Invalid dealer information"}), 401

        log_debug(f"GET /get-customers - Dealer validation successful for dealer_id={dealer_id}, dealer_code={dealer_code}")

        # Query the Opportunity table for customer results
        customer_results = db.session.query(Opportunity).filter_by(dealer_code=dealer_code).all()

        if opportunity_name:
            customer_results = [customer for customer in customer_results if customer.opportunity_name == opportunity_name]

        if not customer_results:
            log_debug(f"GET /get-customers - No customers found for dealer_code={dealer_code} with opportunity_name={opportunity_name}")
            return jsonify({"message": "No customers found for the given dealer code"}), 404

        customer_data = [customer.opportunity_to_dict() for customer in customer_results]
        log_debug(f"GET /get-customers - Found {len(customer_data)} customers for dealer_code={dealer_code}")

        return jsonify({
            "message": "Customers fetched successfully",
            "customers": customer_data
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session on error
        log_error(f"GET /get-customers - Database error occurred: {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        log_error(f"GET /get-customers - Unexpected error occurred: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        db.session.close()
        log_info("GET /get-customers - End of get_all_customers function")

@app.route('/single-customer', methods=['GET'])
def get_single_customer():
    """
    Fetch a single customer's information based on the opportunity ID.
    """
    log_info("GET /single-customer - get_single_customer function has started...")
    try:
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_name = request.args.get('opportunity_name')
        opportunity_id = request.args.get('opportunity_id')

        log_debug(f"GET /single-customer - query parameters: dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_name={opportunity_name}, opportunity_id={opportunity_id}")

        dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code
        ).first()

        if not dealer:
            log_debug(f"GET /single-customer - Invalid dealer information: dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_name={opportunity_name}")
            return jsonify({"error": "Invalid dealer information"}), 401

        log_debug(f"GET /single-customer - Dealer validation successful for dealer_id={dealer_id}, dealer_code={dealer_code}")

        # Query for the customer
        customer = db.session.query(Opportunity).filter_by(
            opportunity_id=opportunity_id
        ).first()

        if not customer:
            log_debug(f"GET /single-customer - No customer found with opportunity_id={opportunity_id}")
            return jsonify({"error": "Customer not found"}), 404

        log_info(f"GET /single-customer - Found customer with opportunity_id={opportunity_id}")

        return jsonify({
            "message": "Customer found",
            "customer": customer.opportunity_to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback on error
        log_error(f"GET /single-customer - Database error occurred: {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        log_error(f"GET /single-customer - Unexpected error occurred: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        db.session.close()
        log_info("GET /single-customer - End of get_single_customer function")
        
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000,debug=True)
