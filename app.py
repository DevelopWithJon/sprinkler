from flask import Flask, jsonify, request, render_template, redirect, url_for
import json
import logging
from datetime import datetime, timezone, timedelta
from Sprinklers import Sprinklers
from api import System

app = Flask(__name__)

today = datetime.now(timezone.utc).isoformat()

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
    today=datetime.now(timezone.utc).isoformat()

    logging.info("Starting get_sprinkler_message function execution")

    results = {"date": "", "message": ""}

    try:
        with open('results.json', 'r') as f:
            logging.info("Opening results.json")
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("results.json not found or invalid. Initializing empty results.")
        

    if not results or results['date']=="" or datetime.fromisoformat(results["date"]).date() != datetime.fromisoformat(today).date():
        logging.info("New execution required for today")
        api_system = System(NOW, LAST_WEEK)
        sprinklers = Sprinklers(api_system)
        message = sprinklers.message()
        
        results = {"date": today, "current_time": today, "message": message}
    else:
        logging.info("Using cached results from today")

    results['current_time'] = today
    with open('results.json', 'w') as f:
            logging.info("Writing new results to results.json")
            json.dump(results, f)
    
    logging.info("get_sprinkler_message function execution completed")
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sprinkler_action', methods=['POST'])
def sprinkler_action():
    today = datetime.now(timezone.utc).isoformat()
    action = request.form.get('action')
    results={}
    if action == 'ON':
        data = {"action": True, "duration": 60000}
    elif action == 'OFF':
        data = {"action": False, "duration": 0}
    
    results["date"] = today
    results["current_time"] = today
    results["message"]=data

    with open('results.json', 'w') as f:
        json.dump(results, f)
    
    return redirect(url_for('index'))

@app.route('/get_message')
def get_message():
    try:
        message = get_sprinkler_message()
        today = datetime.now(timezone.utc).isoformat()
        if isinstance(message, dict) and message['message'].get('action') == True:
            time_diff = (datetime.now(timezone.utc) - datetime.fromisoformat(message.get('date', today))).total_seconds() * 1000  # Convert to microseconds
            if time_diff >= message['message'].get('duration', 0):
                results = {
                    "date": today,
                    "current_time": today,
                    "message": {'action': False, 'duration': 0}
                }
                
                with open('results.json', 'w') as f:
                    logging.info("Writing new results to results.json")
                    json.dump(results, f)
                
                message = results['message']

        response = jsonify({"message": message})
        
        
        return response
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
@app.route('/clear_results', methods=['POST'])
def clear_results():
    try:
        # Overwrite the results.json file with an empty dictionary
        with open('results.json', 'w') as f:
            json.dump({}, f)
        logging.info("results.json file has been cleared (overwritten with empty data)")

        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"An error occurred while clearing results: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)