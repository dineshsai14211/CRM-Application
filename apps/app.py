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


@app.route('/new_customer', methods=["POST"])
def register_new_customer():
    """
    Registers a new customer in the opportunity table.
    :return: JSON response with detailed customer information.
    """
    log_info("[Customer Registration] - Request received to register a new customer.")
    try:
        # Parse the request payload
        data = request.get_json()
        log_debug(f"[Customer Registration] - Received payload: {data}")

        # Generate unique opportunity ID
        generated_opportunity_id = str(uuid.uuid1())
        log_debug(f"[Customer Registration] - Generated Opportunity ID: {generated_opportunity_id}")

        # Get current date and time (without timezone)
        created_timestamp = datetime.now()
        data.update({'created_date': created_timestamp, 'opportunity_id': generated_opportunity_id})
        log_debug(f"[Customer Registration] - After updating created_date and opportunity_id: {data}")

        # Validate account details
        customer_account_name = data.get("account_name")
        if not customer_account_name:
            log_debug("[Customer Registration] - Validation Failed: 'account_name' is missing.")
            return jsonify({"error": "account_name is required"}), 400

        # Check if the account exists
        existing_account = db.session.query(Account).filter_by(account_name=customer_account_name).first()
        if not existing_account:
            # If account doesn't exist, create a new one
            new_account_id = str(uuid.uuid4())  # Generate a new UUID for account
            new_account = Account(
                account_id=new_account_id,
                account_name=customer_account_name
            )
            db.session.add(new_account)
            db.session.commit()
            log_debug(f"[Customer Registration] - New Account Created: Account Name = {customer_account_name}")
        else:
            log_debug(f"[Customer Registration] - Account Found: Account Name = {customer_account_name}")

        # Validate dealer details
        dealer_id = data.get("dealer_id")
        dealer_code = data.get("dealer_code")
        owner = data.get("opportunity_owner")

        if not dealer_id or not dealer_code or not owner:
            log_debug(
                "[Customer Registration] - Validation Failed: dealer_id, dealer_code, or opportunity_owner missing.")
            return jsonify({"error": "dealer_id, dealer_code, and opportunity_owner are required"}), 400

        # Check if the dealer exists
        existing_dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            opportunity_owner=owner
        ).first()

        if not existing_dealer:
            # If dealer doesn't exist, create a new dealer
            new_dealer = Dealer(
                dealer_id=dealer_id,
                dealer_code=dealer_code,
                opportunity_owner=owner
            )
            db.session.add(new_dealer)
            db.session.commit()
            log_debug(
                f"[Customer Registration] - New Dealer Created: Dealer ID = {dealer_id}, Dealer Code = {dealer_code}, Owner = {owner}")
        else:
            log_debug(
                f"[Customer Registration] - Dealer Found: Dealer ID = {dealer_id}, Dealer Code = {dealer_code}, Owner = {owner}")

        # Parse close_date if provided
        close_date = data.get("close_date")
        if close_date:
            try:
                close_date = datetime.strptime(close_date, "%Y-%m-%d %H:%M:%S")
                log_debug(f"[Customer Registration] - Close Date Parsed: {close_date}")
            except ValueError as e:
                log_debug(f"[Customer Registration] - Invalid Date Format for close_date: {str(e)}")
                return jsonify({"error": f"Invalid date format for close_date: {str(e)}"}), 400
        else:
            close_date = None
            log_debug("[Customer Registration] - No Close Date Provided, set to None.")

        # Determine stage from probability
        probability_value = data.get("probability")
        if probability_value is not None:
            try:
                sales_stage = get_probability(probability_value)
                log_debug(f"[Customer Registration] - Stage determined from probability: {sales_stage}")
            except ValueError as e:
                log_debug(f"[Customer Registration] - Invalid probability value: {str(e)}")
                return jsonify({"error": f"Invalid probability value: {str(e)}"}), 400
        else:
            sales_stage = data.get("stage", "Unknown")
            log_debug(f"[Customer Registration] - No probability provided, defaulting stage to: {sales_stage}")

        # Handle currency conversion
        opportunity_amount = data.get("amount")
        if opportunity_amount:
            converted_currency_values = currency_conversion(opportunity_amount)
            log_debug(f"[Customer Registration] - Currency Conversions: {converted_currency_values}")
        else:
            converted_currency_values = {}
            log_debug("[Customer Registration] - No amount provided, skipping currency conversion.")

        # Create a new opportunity record
        new_opportunity_record = Opportunity(
            opportunity_id=generated_opportunity_id,
            opportunity_name=data.get("opportunity_name"),
            account_name=customer_account_name,
            close_date=close_date,
            amount=opportunity_amount,
            description=data.get("description"),
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            stage=sales_stage,
            probability=probability_value,
            next_step=data.get("next_step"),
            created_date=created_timestamp,
            usd=converted_currency_values.get("USD"),
            aus=converted_currency_values.get("AUD"),
            cad=converted_currency_values.get("CAD"),
            amount_in_words=convert_amount_to_word(opportunity_amount)
        )

        log_debug(f"[Customer Registration] - New Opportunity Created: {new_opportunity_record}")
        db.session.add(new_opportunity_record)
        db.session.commit()
        log_debug(f"[Customer Registration] - Opportunity successfully created with ID: {generated_opportunity_id}")

        customer_data = new_opportunity_record.opportunity_to_dict()
        log_debug(f"[Customer Registration] - Serialized customer details: {customer_data}")

        # Return success response with the customer details
        return jsonify({
            "message": "Customer created successfully",
            "customer_details": customer_data
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session in case of a database error
        log_error(f"[Customer Registration] - Database Error: {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        log_error(f"[Customer Registration] - Unexpected Error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        db.session.close()
        log_info("[Customer Registration] - End of function: register_new_customer")


@app.route('/get-customers', methods=['GET'])
def get_all_customers():
    """
    Fetch all customers whose dealer code matches the given dealer code.
    """
    log_info("GET /get-customers - get_all_customers function has started")
    try:
        # Read all the query parameters
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_owner = request.args.get('opportunity_owner')

        log_debug(
            f"GET /get-customers- dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_owner={opportunity_owner}")

        dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            opportunity_owner=opportunity_owner
        ).first()

        if not dealer:
            log_debug(
                f"GET /get-customers- Invalid dealer information: dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_owner={opportunity_owner}")
            return jsonify({"error": "Invalid dealer information"}), 401

        log_debug(
            f"GET /get-customers - Dealer validation successful for dealer_id={dealer_id}, dealer_code={dealer_code}")

        customer_results = db.session.query(Opportunity).filter_by(dealer_code=dealer_code).all()

        if not customer_results:
            log_debug(f"GET /get-customers- No customers found for dealer_code={dealer_code}")
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
    log_info("GET /single-customer - get_single_customer function has stated...")
    try:
        # Read all the query parameters
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_owner = request.args.get('opportunity_owner')
        opportunity_id = request.args.get('opportunity_id')

        log_debug(
            f"GET /single-customer- query parameters: dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_owner={opportunity_owner}, opportunity_id={opportunity_id}")

        dealer = db.session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            opportunity_owner=opportunity_owner
        ).first()

        if not dealer:
            log_debug(
                f"GET /single-customer - Invalid dealer information: dealer_id={dealer_id}, dealer_code={dealer_code}, opportunity_owner={opportunity_owner}")
            return jsonify({"error": "Invalid dealer information"}), 401

        log_debug(
            f"GET /single-customer- Dealer validation successful for dealer_id={dealer_id}, dealer_code={dealer_code}")

        customer = db.session.query(Opportunity).filter_by(opportunity_id=opportunity_id).first()

        if not customer:
            log_debug(f"GET /single-customer - No customer found for opportunity_id={opportunity_id}")
            return jsonify({"message": "No customer found for the given opportunity ID"}), 404

        customer_data = customer.opportunity_to_dict()
        log_debug(f"GET /single-customer- Customer data retrieved for opportunity_id={opportunity_id}")

        return jsonify({
            "message": "Customer fetched successfully",
            "customer": customer_data
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session on error
        log_error(f"GET /single-customer Database error occurred: {str(e)}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        log_error(f"GET /single-customer - Unexpected error occurred: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        db.session.close()
        log_info("GET /single-customer- End of get_single_customer function")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
