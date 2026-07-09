import os
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras # Used for DictCursor

# --- Database Configuration ---
# NOTE: YOU MUST REPLACE THE STRING BELOW with the actual password 
# for your PostgreSQL 'postgres' user. This is the source of the FATAL error.
DB_HOST = "localhost"
DB_NAME = "metro_db"
DB_USER = "postgres"
DB_PASS = "Binoviini@14" # <--- REPLACE THIS STRING WITH YOUR PASSWORD
DB_PORT = "5432"

app = Flask(__name__)

# --- Database Connection and Utility Functions ---

def get_db_connection():
    """Establishes and returns a PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        # Use DictCursor to fetch results as dictionaries instead of tuples
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        traceback.print_exc()
        return None

def fetch_data(query, params=None):
    """Executes a SELECT query and returns results as a list of dictionaries."""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            # Convert DictRow objects to standard dictionaries for JSON serialization
            results = [dict(row) for row in cur.fetchall()]
            return results
    except Exception as e:
        print(f"Error executing fetch query: {e}")
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()

def execute_query(query, params=None, fetch_id=False):
    """Executes an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection error"

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch_id:
                # Used for getting the ID of a newly inserted row
                new_id = cur.fetchone()[0]
                conn.commit()
                return True, new_id
            
            conn.commit()
            return True, cur.rowcount # Return rowcount for update/delete
    except Exception as e:
        print(f"Error executing CUD query: {e}")
        traceback.print_exc()
        # Check for specific error codes related to integrity/constraint issues
        if isinstance(e, psycopg2.IntegrityError) and "violates not-null constraint" in str(e):
             error_message = "Data integrity error: Primary Key (ID) may be missing its auto-increment sequence (SERIAL)."
        elif isinstance(e, psycopg2.IntegrityError):
             error_message = f"Data integrity error: {str(e).splitlines()[0]}"
        else:
             error_message = str(e)

        conn.rollback()
        return False, error_message
    finally:
        if conn:
            conn.close()

# --- Utility for Table Name Mapping (matches original CSV structure) ---
# NOTE: The tables are assumed to be named exactly 'trains', 'maintenance', 'advertisements'

TRAIN_TABLE = "trains"
MAINTENANCE_TABLE = "maintenance"
ADS_TABLE = "advertisements"


# --- FLASK ROUTES (API Endpoints) ---

@app.route('/')
def index():
    """Serves the main HTML file."""
    try:
        # Assuming you have an 'index.html' template
        return render_template('index.html') 
    except Exception as e:
        print(f"Error rendering template: {e}")
        return "Error loading page template.", 500


# --- GET Endpoints ---

@app.route('/api/trains', methods=['GET'])
def get_trains():
    """API endpoint to get all trains."""
    query = f"SELECT train_id, train_number, home_location, status FROM {TRAIN_TABLE} ORDER BY train_id;"
    trains = fetch_data(query)
    if trains is None:
        return jsonify({"error": "Failed to retrieve trains from database"}), 500
    return jsonify(trains)

@app.route('/api/maintenance', methods=['GET'])
def get_maintenance_records():
    """API endpoint to get all maintenance records."""
    query = f"SELECT record_id, train_id, issue, date_reported, severity, status FROM {MAINTENANCE_TABLE} ORDER BY date_reported DESC;"
    records = fetch_data(query)
    if records is None:
        return jsonify({"error": "Failed to retrieve maintenance records from database"}), 500
    # Convert datetime objects to string format for JSON
    for record in records:
        if isinstance(record.get('date_reported'), datetime):
             record['date_reported'] = record['date_reported'].strftime('%Y-%m-%d')
    return jsonify(records)

@app.route('/api/ads', methods=['GET'])
def get_advertisements():
    """API endpoint to get all advertisement campaigns."""
    query = f"SELECT ad_id, train_id, brand_name, start_date, end_date, priority FROM {ADS_TABLE} ORDER BY ad_id;"
    ads = fetch_data(query)
    if ads is None:
        return jsonify({"error": "Failed to retrieve advertisements from database"}), 500
    # Convert date/datetime objects to string format for JSON
    for ad in ads:
        if ad.get('start_date'): ad['start_date'] = ad['start_date'].strftime('%Y-%m-%d')
        if ad.get('end_date'): ad['end_date'] = ad['end_date'].strftime('%Y-%m-%d')
    return jsonify(ads)


@app.route('/api/trains/<int:train_id>/history', methods=['GET'])
def get_train_history(train_id):
    """API endpoint to get history for a specific train."""
    
    # 1. Get Train Details
    train_query = f"SELECT train_id, train_number, home_location, status FROM {TRAIN_TABLE} WHERE train_id = %s;"
    train_details = fetch_data(train_query, (train_id,))
    if not train_details:
        return jsonify({"error": "Train not found"}), 404
    train_details = train_details[0]

    # 2. Get Maintenance History
    maintenance_query = f"SELECT record_id, issue, date_reported, severity, status FROM {MAINTENANCE_TABLE} WHERE train_id = %s ORDER BY date_reported DESC;"
    maintenance_history = fetch_data(maintenance_query, (train_id,))
    # Convert datetime to string
    if maintenance_history:
        for record in maintenance_history:
            if isinstance(record.get('date_reported'), datetime):
                 record['date_reported'] = record['date_reported'].strftime('%Y-%m-%d')

    # 3. Get Ad History
    ad_query = f"SELECT ad_id, brand_name, start_date, end_date, priority FROM {ADS_TABLE} WHERE train_id = %s ORDER BY ad_id;"
    ad_history = fetch_data(ad_query, (train_id,))
    # Convert date to string
    if ad_history:
        for ad in ad_history:
            if ad.get('start_date'): ad['start_date'] = ad['start_date'].strftime('%Y-%m-%d')
            if ad.get('end_date'): ad['end_date'] = ad['end_date'].strftime('%Y-%m-%d')


    return jsonify({
        "details": train_details,
        "maintenance": maintenance_history,
        "advertisements": ad_history
    })

# --- POST Endpoints (Add) ---

@app.route('/api/trains/add', methods=['POST'])
def add_train():
    """API endpoint to add a new train."""
    data = request.json
    if not data or not data.get('train_number') or not data.get('home_location'):
        return jsonify({"success": False, "message": "Missing train_number or home_location"}), 400
    
    train_number = data['train_number']
    
    # Check for duplicate train_number
    check_query = f"SELECT train_id FROM {TRAIN_TABLE} WHERE train_number = %s;"
    existing_train = fetch_data(check_query, (train_number,))
    if existing_train:
         return jsonify({"success": False, "message": f"Train number '{train_number}' already exists."}), 409

    # Insert new train
    insert_query = f"INSERT INTO {TRAIN_TABLE} (train_number, home_location, status) VALUES (%s, %s, %s) RETURNING train_id;"
    success, result = execute_query(insert_query, (train_number, data['home_location'], "Available"), fetch_id=True)
    
    if success:
        new_train_id = result
        new_train = {
            "train_id": new_train_id,
            "train_number": train_number,
            "home_location": data['home_location'],
            "status": "Available"
        }
        return jsonify({"success": True, "train": new_train}), 201
    else:
        # result now contains the detailed error message from execute_query
        return jsonify({"success": False, "message": f"Failed to add train. Database Error: {result}"}), 500


@app.route('/api/maintenance/add', methods=['POST'])
def add_maintenance():
    """API endpoint to add a maintenance record."""
    data = request.json
    if not data or data.get('train_id') is None or data.get('issue') is None or data.get('severity') is None:
         return jsonify({"success": False, "message": "Missing required fields: train_id, issue, severity"}), 400

    try:
        train_id = int(data['train_id'])
        severity = int(data['severity'])
        if not 1 <= severity <= 10:
            return jsonify({"success": False, "message": "Severity must be between 1 and 10."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "train_id and severity must be valid numbers."}), 400

    # Insert new maintenance record
    insert_query = f"INSERT INTO {MAINTENANCE_TABLE} (train_id, issue, date_reported, severity, status) VALUES (%s, %s, %s, %s, %s) RETURNING record_id;"
    current_date = datetime.now().strftime('%Y-%m-%d')
    success, result = execute_query(
        insert_query, 
        (train_id, data['issue'], current_date, severity, "Pending"), 
        fetch_id=True
    )
    
    if success:
        new_record_id = result
        
        # Auto-update train status if severe (severity >= 7)
        if severity >= 7:
            update_query = f"UPDATE {TRAIN_TABLE} SET status = 'In-Maintenance' WHERE train_id = %s AND status != 'In-Maintenance';"
            execute_query(update_query, (train_id,)) # Not checking success, as it's a non-critical side effect

        new_record = {
            "record_id": new_record_id,
            "train_id": train_id,
            "issue": data['issue'],
            "date_reported": current_date,
            "severity": severity,
            "status": "Pending"
        }
        return jsonify({"success": True, "record": new_record}), 201
    else:
        return jsonify({"success": False, "message": f"Failed to add maintenance record. Database Error: {result}"}), 500


@app.route('/api/ads/add', methods=['POST'])
def add_advertisement():
    """API endpoint to add an advertisement (contract)."""
    data = request.json
    required_fields = ['train_id', 'brand_name', 'start_date', 'end_date', 'priority']
    if not data or not all(field in data and data[field] is not None for field in required_fields):
         missing = [f for f in required_fields if not data.get(f)]
         return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        train_id = int(data['train_id'])
        start_date_obj = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        priority = int(data['priority'])
        
        if end_date_obj < start_date_obj:
             return jsonify({"success": False, "message": "End date cannot be before start date."}), 400
        if priority not in [1, 2, 3]:
            return jsonify({"success": False, "message": "Priority must be 1 (Low), 2 (Medium), or 3 (High)."}), 400

    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "train_id must be a valid number, dates must be YYYY-MM-DD, priority must be 1, 2, or 3."}), 400

    # Insert new advertisement
    insert_query = f"INSERT INTO {ADS_TABLE} (train_id, brand_name, start_date, end_date, priority) VALUES (%s, %s, %s, %s, %s) RETURNING ad_id;"
    success, result = execute_query(
        insert_query, 
        (train_id, data['brand_name'], data['start_date'], data['end_date'], priority), 
        fetch_id=True
    )
    
    if success:
        new_ad_id = result
        new_ad = {
            "ad_id": new_ad_id,
            "train_id": train_id,
            "brand_name": data['brand_name'],
            "start_date": data['start_date'],
            "end_date": data['end_date'],
            "priority": priority
        }
        return jsonify({"success": True, "ad": new_ad}), 201
    else:
        return jsonify({"success": False, "message": f"Failed to add advertisement. Database Error: {result}"}), 500


# --- DELETE Endpoints ---

@app.route('/api/trains/delete/<int:train_id>', methods=['DELETE'])
def delete_train(train_id):
    """API endpoint to delete a train and related records (Database)."""
    try:
        # Delete related records first (Maintenance and Ads)
        # Note: In a real system, setting up CASCADE DELETE foreign keys is better,
        # but for simplicity, we use explicit deletes here.
        execute_query(f"DELETE FROM {MAINTENANCE_TABLE} WHERE train_id = %s;", (train_id,))
        execute_query(f"DELETE FROM {ADS_TABLE} WHERE train_id = %s;", (train_id,))

        # Delete the train itself
        delete_train_query = f"DELETE FROM {TRAIN_TABLE} WHERE train_id = %s;"
        success, row_count = execute_query(delete_train_query, (train_id,))
        
        if success and row_count > 0:
            return jsonify({"success": True, "message": f"Train {train_id} and associated records deleted."})
        elif success and row_count == 0:
            return jsonify({"success": False, "message": "Train not found."}), 404
        else:
            return jsonify({"success": False, "message": f"Server error deleting train: {row_count}"}), 500

    except Exception as e:
        print(f"Error deleting train {train_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting train: {str(e)}"}), 500


@app.route('/api/maintenance/delete/<int:record_id>', methods=['DELETE'])
def delete_maintenance(record_id):
    """API endpoint to delete a maintenance record and update train status if necessary."""
    try:
        # 1. Get train_id and severity before deleting
        record_query = f"SELECT train_id, severity FROM {MAINTENANCE_TABLE} WHERE record_id = %s;"
        record_to_delete = fetch_data(record_query, (record_id,))
        
        if not record_to_delete:
            return jsonify({"success": False, "message": "Maintenance record not found."}), 404
            
        train_id_affected = record_to_delete[0]['train_id']
        severity_deleted = record_to_delete[0]['severity']

        # 2. Delete the record
        delete_query = f"DELETE FROM {MAINTENANCE_TABLE} WHERE record_id = %s;"
        success, row_count = execute_query(delete_query, (record_id,))
        
        if not success or row_count == 0:
             return jsonify({"success": False, "message": "Failed to delete maintenance record or record not found."}), 500

        # 3. Check for train status update (only if the deleted record was severe)
        if severity_deleted >= 7:
            # Check if there are any other high-severity, pending issues for this train
            check_high_sev_query = f"SELECT COUNT(*) FROM {MAINTENANCE_TABLE} WHERE train_id = %s AND status = 'Pending' AND severity >= 7;"
            remaining_high_sev = fetch_data(check_high_sev_query, (train_id_affected,))
            
            if remaining_high_sev and remaining_high_sev[0]['count'] == 0:
                # No other severe pending issues, change train status back to Available
                update_train_query = f"UPDATE {TRAIN_TABLE} SET status = 'Available' WHERE train_id = %s AND status = 'In-Maintenance';"
                execute_query(update_train_query, (train_id_affected,))

        return jsonify({"success": True, "message": f"Maintenance record {record_id} deleted."})

    except Exception as e:
        print(f"Error deleting maintenance record {record_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting maintenance record: {str(e)}"}), 500


@app.route('/api/ads/delete/<int:ad_id>', methods=['DELETE'])
def delete_ad(ad_id):
    """API endpoint to delete an advertisement contract (Database)."""
    try:
        delete_query = f"DELETE FROM {ADS_TABLE} WHERE ad_id = %s;"
        success, row_count = execute_query(delete_query, (ad_id,))
        
        if success and row_count > 0:
            return jsonify({"success": True, "message": f"Advertisement contract {ad_id} deleted."})
        else:
            return jsonify({"success": False, "message": "Advertisement contract not found."}), 404

    except Exception as e:
        print(f"Error deleting ad {ad_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting ad: {str(e)}"}), 500


# --- COMPLEX LOGIC Endpoints ---

@app.route('/api/schedule/generate', methods=['POST'])
def generate_schedule():
    """API endpoint to generate the daily schedule, querying DB for conflicts."""
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # 1. Fetch all necessary data with one query (using a view or a complex JOIN is better,
        # but two simple queries are cleaner for this example)

        # Get all trains
        trains_query = f"SELECT train_id, train_number, home_location, status FROM {TRAIN_TABLE};"
        all_trains = fetch_data(trains_query)

        # Get all relevant maintenance issues (Pending)
        maintenance_query = f"SELECT train_id, severity, status, issue FROM {MAINTENANCE_TABLE} WHERE status = 'Pending';"
        all_maintenance = fetch_data(maintenance_query)

        # Get all currently active ads
        ads_query = f"SELECT train_id, brand_name, priority FROM {ADS_TABLE} WHERE start_date <= %s AND end_date >= %s;"
        all_ads = fetch_data(ads_query, (today, today))

        if all_trains is None or all_maintenance is None or all_ads is None:
             return jsonify({"error": "Failed to fetch necessary data from database"}), 500

        # --- Data Processing and Scheduling Logic ---

        # Pre-process maintenance and ads into dictionaries for fast lookup
        maintenance_map = {} # {train_id: {highest_severity: X, details: {...}}}
        for record in all_maintenance:
            tid = record['train_id']
            sev = record['severity']
            if tid not in maintenance_map or sev > maintenance_map[tid]['highest_severity']:
                maintenance_map[tid] = {'highest_severity': sev, 'details': record}

        ad_map = {} # {train_id: {highest_priority: X, details: {...}}}
        for ad in all_ads:
            tid = ad['train_id']
            priority = ad['priority']
            if tid not in ad_map or priority > ad_map[tid]['highest_priority']:
                ad_map[tid] = {'highest_priority': priority, 'details': ad}


        operating_trains = []
        conflicts_found = []
        priority_text_map_backend = {1: 'Low', 2: 'Medium', 3: 'High'}


        for train in all_trains:
            train_id = train['train_id']
            
            highest_pending_severity = maintenance_map.get(train_id, {}).get('highest_severity', 0)
            pending_issue_details = maintenance_map.get(train_id, {}).get('details')
            
            highest_active_ad_priority = ad_map.get(train_id, {}).get('highest_priority', 0)
            active_ad_details = ad_map.get(train_id, {}).get('details')
            
            should_run = False
            must_be_maintained = False 

            if highest_pending_severity == 0:
                # No pending issues, always run
                should_run = True
            elif highest_pending_severity <= 6:
                # Low/Medium severity issues (1-6), allow running
                should_run = True
            elif highest_pending_severity == 7:
                # Severe issue (7): run if high priority ad (2/3) is active
                if highest_active_ad_priority >= 2: 
                    should_run = True 
                    must_be_maintained = True # Flag as a conflict
                
            elif highest_pending_severity == 8:
                # Critical issue (8): run only if highest priority ad (3) is active
                if highest_active_ad_priority >= 3: 
                    should_run = True 
                    must_be_maintained = True # Flag as a conflict
            
            # Issues 9 or 10: Never run
            # If highest_pending_severity >= 9, should_run remains False

            if should_run:
                operating_trains.append(train)
                
                if must_be_maintained and active_ad_details and pending_issue_details:
                    ad_priority_str_val = active_ad_details.get('priority', 0)
                    ad_priority_str_text = priority_text_map_backend.get(ad_priority_str_val, 'N/A')
                    
                    conflict_msg = (
                        f"Train no {train.get('train_number', 'N/A')} is running with HIGH CONFLICT: "
                        f"Ad Priority: {ad_priority_str_text} ({ad_priority_str_val}). "
                        f"Maintenance Severity: {highest_pending_severity}. "
                        f"Issue: {pending_issue_details.get('issue', 'N/A')}"
                    )
                    conflicts_found.append(conflict_msg)


        # --- Time Table Generation ---

        timetable = []
        calculated_frequency = 0
        if operating_trains:
            calculated_frequency = round(120 / len(operating_trains), 2) if len(operating_trains) > 0 else 0
            
            if calculated_frequency > 0:
                start_time = datetime.strptime("05:00", "%H:%M")
                end_time = datetime.strptime("23:00", "%H:%M")
                current_time = start_time
                train_index = 0
                
                # Prevent infinite loops in edge cases
                max_iterations = 1000 
                iterations = 0
                
                while current_time < end_time and iterations < max_iterations:
                    train_on_duty = operating_trains[train_index]
                    timetable.append({
                        "time": current_time.strftime('%H:%M'),
                        "train_number": train_on_duty.get('train_number', 'N/A'),
                        "train_id": train_on_duty.get('train_id', 'N/A')
                    })
                    
                    # Ensure frequency is at least 1 minute to prevent overly small time steps
                    safe_frequency = max(1.0, calculated_frequency) 
                    current_time += timedelta(minutes=safe_frequency)
                    train_index = (train_index + 1) % len(operating_trains)
                    iterations += 1
                
                if iterations >= max_iterations: print("Warning: Schedule generation hit max iterations limit.")

        return jsonify({
            "schedule": timetable,
            "conflicts": conflicts_found, 
            "frequency": calculated_frequency
        })

    except Exception as e:
        print(f"Error generating schedule: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate schedule: {str(e)}"}), 500


if __name__ == '__main__':
    # Initialize the database connection once here (it won't do much, but serves as a basic check)
    conn = get_db_connection()
    if conn:
        print("Successfully connected to PostgreSQL database: metro_db")
        conn.close()
    else:
        print("Starting Flask app, but DB connection failed. Check config and PostgreSQL server.")
        
    app.run(debug=True, port=5000)
