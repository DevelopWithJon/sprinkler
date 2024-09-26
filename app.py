from flask import Flask, jsonify, request, render_template, redirect, url_for
import json
import logging
from datetime import datetime, timezone, timedelta
from Sprinklers import Sprinklers
from api import System

app = Flask(__name__)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler('sprinkler_system.log')
console_handler = logging.StreamHandler()

# Set level for handlers
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_sprinkler_message():
    NOW = datetime.now(timezone.utc)
    LAST_WEEK = NOW.date() - timedelta(days=30)
    today = NOW.date().isoformat()

    logging.info("Starting get_sprinkler_message function execution")

    results = {"date": "", "message": ""}

    try:
        with open('results.json', 'r') as f:
            logging.info("Opening results.json")
            results = json.load(f)
            print("results: ",results)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("results.json not found or invalid. Initializing empty results.")
        
    
    if results["date"] != today:
        logging.info("New execution required for today")
        api_system = System(NOW, LAST_WEEK)
        sprinklers = Sprinklers(api_system)
        message = sprinklers.message()
        
        results = {"date": today, "message": message}
        with open('results.json', 'w') as f:
            logging.info("Writing new results to results.json")
            json.dump(results, f)
    else:
        logging.info("Using cached results from today")
    
    logging.info("get_sprinkler_message function execution completed")
    return results["message"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sprinkler_action', methods=['POST'])
def sprinkler_action():
    today = datetime.now(timezone.utc).date().isoformat()
    action = request.form.get('action')
    results={}
    if action == 'ON':
        data = {"action": True, "duration": 60000}
    elif action == 'OFF':
        data = {"action": False, "duration": 0}
    
    results["date"] = today
    results["message"]=data

    with open('results.json', 'w') as f:
        json.dump(results, f)
    
    return redirect(url_for('index'))

@app.route('/get_message')
def get_message():
    try:
        message = get_sprinkler_message()
        return jsonify({"message": message})
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)