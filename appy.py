import csv
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import traceback 
DATA_DIR = "metro_data"
TRAINS_FILE = os.path.join(DATA_DIR, "trains.csv")
MAINTENANCE_FILE = os.path.join(DATA_DIR, "maintenance.csv")
ADS_FILE = os.path.join(DATA_DIR, "advertisements.csv")

TRAIN_HEADERS = ["train_id", "train_number", "home_location", "status"]
MAINTENANCE_HEADERS = ["record_id", "train_id", "issue", "date_reported", "severity", "status"]
AD_HEADERS = ["ad_id", "train_id", "brand_name", "start_date", "end_date", "priority"]

app = Flask(__name__)

def initialize_data_files():
    """Ensures the data directory and CSV files exist with headers."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(TRAINS_FILE):
            write_to_csv(TRAINS_FILE, [], TRAIN_HEADERS)
        if not os.path.exists(MAINTENANCE_FILE):
            write_to_csv(MAINTENANCE_FILE, [], MAINTENANCE_HEADERS)
        if not os.path.exists(ADS_FILE):
            write_to_csv(ADS_FILE, [], AD_HEADERS)
    except Exception as e:
        print(f"ERROR: Could not initialize data files: {e}")


def read_from_csv(file_path):
    """Reads all rows from a CSV file and returns them as a list of dictionaries."""
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            return [row for row in reader if any(field and field.strip() for field in row.values())]
    except FileNotFoundError:
        print(f"Warning: File not found {file_path}. Returning empty list.")
        return []
    except Exception as e:
        print(f"ERROR reading CSV {file_path}: {e}")
        traceback.print_exc()
        return [] # Return empty list on other errors too


def write_to_csv(file_path, data, headers):
    try:
        valid_data = []
        for row in data:
            filtered_row = {header: row.get(header, '') for header in headers}
            valid_data.append(filtered_row)

        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(valid_data) 
    except Exception as e:
        print(f"ERROR writing CSV {file_path}: {e}")
        traceback.print_exc()

@app.route('/')
def index():
    """Serves the main HTML file."""
    initialize_data_files()
    try:
        return render_template('index.html') 
    except Exception as e:
        print(f"Error rendering template: {e}")
        return "Error loading page template.", 500


@app.route('/api/trains', methods=['GET'])
def get_trains():
    """API endpoint to get all trains."""
    trains = read_from_csv(TRAINS_FILE)
    return jsonify(trains)

@app.route('/api/maintenance', methods=['GET'])
def get_maintenance_records():
    """API endpoint to get all maintenance records."""
    records = read_from_csv(MAINTENANCE_FILE)
    return jsonify(records)

@app.route('/api/ads', methods=['GET'])
def get_advertisements():
    """API endpoint to get all advertisement campaigns."""
    ads = read_from_csv(ADS_FILE)
    return jsonify(ads)

@app.route('/api/trains/<int:train_id>/history', methods=['GET'])
def get_train_history(train_id):
    """API endpoint to get history for a specific train."""
    train_id_str = str(train_id)
    all_trains = read_from_csv(TRAINS_FILE)
    all_maintenance = read_from_csv(MAINTENANCE_FILE)
    all_ads = read_from_csv(ADS_FILE)

    train_details = next((t for t in all_trains if t.get('train_id') == train_id_str), None)
    if not train_details:
        return jsonify({"error": "Train not found"}), 404

    maintenance_history = [m for m in all_maintenance if m.get('train_id') == train_id_str]
    ad_history = [a for a in all_ads if a.get('train_id') == train_id_str]

    return jsonify({
        "details": train_details,
        "maintenance": maintenance_history,
        "advertisements": ad_history
    })

@app.route('/api/trains/add', methods=['POST'])
def add_train():
    """API endpoint to add a new train."""
    try:
        data = request.json
        if not data or not data.get('train_number') or not data.get('home_location'):
            return jsonify({"success": False, "message": "Missing train_number or home_location"}), 400

        all_trains = read_from_csv(TRAINS_FILE)

        # Check for duplicate train_number before adding
        if any(t.get('train_number') == data['train_number'] for t in all_trains):
            return jsonify({"success": False, "message": f"Train number '{data['train_number']}' already exists."}), 409

        new_id = 0
        if all_trains:
             valid_ids = [int(t['train_id']) for t in all_trains if t.get('train_id') and t['train_id'].isdigit()]
             if valid_ids:
                 new_id = max(valid_ids)
        new_id += 1

        new_train = {
            "train_id": str(new_id), # Store IDs as strings
            "train_number": data['train_number'],
            "home_location": data['home_location'],
            "status": "Available"
        }
        all_trains.append(new_train)
        write_to_csv(TRAINS_FILE, all_trains, TRAIN_HEADERS)
        return jsonify({"success": True, "train": new_train}), 201
    except Exception as e:
        print(f"Error adding train: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Failed to add train: {e}"}), 500


@app.route('/api/maintenance/add', methods=['POST'])
def add_maintenance():
    """API endpoint to add a maintenance record."""
    try:
        data = request.json
        if not data or data.get('train_id') is None or data.get('issue') is None or data.get('severity') is None:
             return jsonify({"success": False, "message": "Missing required fields: train_id, issue, severity"}), 400

        try:
            if 'train_id' not in data or data['train_id'] is None: raise ValueError("train_id is missing")
            train_id_to_update_str = str(data['train_id'])
            if 'severity' not in data or data['severity'] is None: raise ValueError("severity is missing")
            severity = int(data['severity'])
            if not 1 <= severity <= 10:
                return jsonify({"success": False, "message": "Severity must be between 1 and 10."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "train_id and severity must be valid numbers."}), 400

        all_trains = read_from_csv(TRAINS_FILE)
        if not any(t.get('train_id') == train_id_to_update_str for t in all_trains):
             print(f"Warning: Adding maintenance for non-existent train ID {train_id_to_update_str}")

        all_maintenance = read_from_csv(MAINTENANCE_FILE)

        new_id = 0
        if all_maintenance:
             valid_ids = [int(m['record_id']) for m in all_maintenance if m.get('record_id') and m['record_id'].isdigit()]
             if valid_ids: new_id = max(valid_ids)
        new_id += 1

        new_record = {
            "record_id": str(new_id),
            "train_id": train_id_to_update_str,
            "issue": data['issue'],
            "date_reported": datetime.now().strftime('%Y-%m-%d'),
            "severity": str(severity),
            "status": "Pending"
        }
        all_maintenance.append(new_record)
        write_to_csv(MAINTENANCE_FILE, all_maintenance, MAINTENANCE_HEADERS)

        # Auto-update train status if severe (severity >= 7)
        train_status_updated = False
        if severity >= 7:
            all_trains = read_from_csv(TRAINS_FILE) 
            for train in all_trains:
                if train.get('train_id') == train_id_to_update_str:
                    train['status'] = 'In-Maintenance'
                    train_status_updated = True
                    break
            if train_status_updated:
                write_to_csv(TRAINS_FILE, all_trains, TRAIN_HEADERS)

        return jsonify({"success": True, "record": new_record}), 201

    except Exception as e:
        print(f"Error adding maintenance record: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error adding maintenance record: {str(e)}"}), 500


@app.route('/api/ads/add', methods=['POST'])
def add_advertisement():
    """API endpoint to add an advertisement (contract)."""
    try:
        data = request.json
        required_fields = ['train_id', 'brand_name', 'start_date', 'end_date', 'priority']
        if not data or not all(field in data and data[field] is not None for field in required_fields):
             missing = [f for f in required_fields if not data.get(f)]
             return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

        try:
            if 'train_id' not in data or data['train_id'] is None: raise ValueError("train_id is missing")
            train_id_to_link_str = str(data['train_id'])
            start_date_obj = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if end_date_obj < start_date_obj:
                 return jsonify({"success": False, "message": "End date cannot be before start date."}), 400
            
            if data['priority'] not in ['1', '2', '3']:
                return jsonify({"success": False, "message": "Priority must be '1' (Low), '2' (Medium), or '3' (High)."}), 400
           

        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "train_id must be a valid number, dates must be YYYY-MM-DD."}), 400

        all_trains = read_from_csv(TRAINS_FILE)
        if not any(t.get('train_id') == train_id_to_link_str for t in all_trains):
            print(f"Warning: Adding ad for non-existent train ID {train_id_to_link_str}")

        all_ads = read_from_csv(ADS_FILE)

        new_id = 0
        if all_ads:
            valid_ids = [int(ad['ad_id']) for ad in all_ads if ad.get('ad_id') and ad['ad_id'].isdigit()]
            if valid_ids: new_id = max(valid_ids)
        new_id += 1

        new_ad = {
            "ad_id": str(new_id),
            "train_id": train_id_to_link_str,
            "brand_name": data['brand_name'],
            "start_date": data['start_date'],
            "end_date": data['end_date'],
            "priority": data['priority'] # This now saves "1", "2", or "3"
        }
        all_ads.append(new_ad)
        write_to_csv(ADS_FILE, all_ads, AD_HEADERS)

        return jsonify({"success": True, "ad": new_ad}), 201

    except Exception as e:
        print(f"Error adding advertisement: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error adding advertisement: {str(e)}"}), 500


@app.route('/api/trains/delete/<int:train_id>', methods=['DELETE'])
def delete_train(train_id):
    """API endpoint to delete a train and related records (CSV)."""
    try:
        train_id_str = str(train_id)
        all_trains = read_from_csv(TRAINS_FILE)
        original_length = len(all_trains)
        all_trains = [t for t in all_trains if t.get('train_id') != train_id_str]

        if len(all_trains) < original_length:
            all_maintenance = read_from_csv(MAINTENANCE_FILE)
            all_maintenance = [m for m in all_maintenance if m.get('train_id') != train_id_str]
            write_to_csv(MAINTENANCE_FILE, all_maintenance, MAINTENANCE_HEADERS)
            all_ads = read_from_csv(ADS_FILE)
            all_ads = [a for a in all_ads if a.get('train_id') != train_id_str]
            write_to_csv(ADS_FILE, all_ads, AD_HEADERS)
            write_to_csv(TRAINS_FILE, all_trains, TRAIN_HEADERS)
            return jsonify({"success": True, "message": f"Train {train_id} and associated records deleted."})
        else:
            return jsonify({"success": False, "message": "Train not found."}), 404
    except Exception as e:
        print(f"Error deleting train {train_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting train: {str(e)}"}), 500


@app.route('/api/maintenance/delete/<int:record_id>', methods=['DELETE'])
def delete_maintenance(record_id):
    """API endpoint to delete a maintenance record (CSV)."""
    try:
        record_id_str = str(record_id)
        all_maintenance = read_from_csv(MAINTENANCE_FILE)
        record_to_delete = next((m for m in all_maintenance if m.get('record_id') == record_id_str), None)

        if record_to_delete:
            train_id_affected = record_to_delete.get('train_id') # String ID
            try: severity_deleted = int(record_to_delete.get('severity', 0))
            except ValueError: severity_deleted = 0

            all_maintenance = [m for m in all_maintenance if m.get('record_id') != record_id_str]
            write_to_csv(MAINTENANCE_FILE, all_maintenance, MAINTENANCE_HEADERS)

            if severity_deleted >= 7 and train_id_affected:
                other_high_sev_pending = False
                for m in all_maintenance: # Check UPDATED list
                    if m.get('train_id') == train_id_affected and m.get('status') == 'Pending':
                        try:
                            if int(m.get('severity', 0)) >= 7: other_high_sev_pending = True; break
                        except ValueError: continue
                if not other_high_sev_pending:
                    all_trains = read_from_csv(TRAINS_FILE)
                    train_updated = False
                    for train in all_trains:
                         if train.get('train_id') == train_id_affected and train.get('status') == 'In-Maintenance':
                             train['status'] = 'Available'; train_updated = True; break
                    if train_updated: write_to_csv(TRAINS_FILE, all_trains, TRAIN_HEADERS)

            return jsonify({"success": True, "message": f"Maintenance record {record_id} deleted."})
        else:
            return jsonify({"success": False, "message": "Maintenance record not found."}), 404
    except Exception as e:
        print(f"Error deleting maintenance record {record_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting maintenance record: {str(e)}"}), 500


@app.route('/api/ads/delete/<int:ad_id>', methods=['DELETE'])
def delete_ad(ad_id):
    """API endpoint to delete an advertisement contract (CSV)."""
    try:
        ad_id_str = str(ad_id)
        all_ads = read_from_csv(ADS_FILE)
        original_length = len(all_ads)
        all_ads = [a for a in all_ads if a.get('ad_id') != ad_id_str]

        if len(all_ads) < original_length:
            write_to_csv(ADS_FILE, all_ads, AD_HEADERS)
            return jsonify({"success": True, "message": f"Advertisement contract {ad_id} deleted."})
        else:
            return jsonify({"success": False, "message": "Advertisement contract not found."}), 404
    except Exception as e:
        print(f"Error deleting ad {ad_id}: {e}"); traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error deleting ad: {str(e)}"}), 500


@app.route('/api/schedule/generate', methods=['POST'])
def generate_schedule():
    """API endpoint to generate the daily schedule with corrected logic."""
    try:
        all_trains = read_from_csv(TRAINS_FILE)
        all_maintenance = read_from_csv(MAINTENANCE_FILE)
        all_ads = read_from_csv(ADS_FILE)

        operating_trains = []
        conflicts_found = []
        today = datetime.now().date()
        
        priority_text_map_backend = {'1': 'Low', '2': 'Medium', '3': 'High'}

        for train in all_trains:
            if not train.get('train_id') or not train.get('status'):
                continue 
            
            # First, check the train's master status. If it's 'In-Maintenance',
            # it should not be considered for the schedule at all.
            if train['status'] == 'In-Maintenance':
                continue 
            
            train_id_str = train['train_id']

            highest_pending_severity = 0
            pending_issue_details = None 
            for record in all_maintenance:
                if record.get('train_id') == train_id_str and record.get('status') == 'Pending':
                    try:
                        current_severity = int(record.get('severity', 0))
                        if current_severity > highest_pending_severity:
                            highest_pending_severity = current_severity
                            pending_issue_details = record 
                    except (ValueError, TypeError):
                        continue 

            highest_active_ad_priority_level = 0
            active_ad_details = None 
            for ad in all_ads:
                if (ad.get('train_id') == train_id_str and
                    ad.get('start_date') and ad.get('end_date') and
                    ad.get('priority') in ['1', '2', '3']):
                    try:
                        start = datetime.strptime(ad['start_date'], '%Y-%m-%d').date()
                        end = datetime.strptime(ad['end_date'], '%Y-%m-%d').date()

                        if start <= today <= end:
                            current_ad_priority_level = int(ad.get('priority', 0))
                            
                            if current_ad_priority_level > highest_active_ad_priority_level:
                                highest_active_ad_priority_level = current_ad_priority_level
                                active_ad_details = ad

                    except (ValueError, TypeError):
                        print(f"Warning: Invalid date or priority format in ad ID {ad.get('ad_id')} for train {train_id_str}")
                        continue 
            should_run = False
            must_be_maintained = False 
            conflict_msg = None

            # This logic now only applies to 'Available' trains
            if highest_pending_severity <= 6:
                should_run = True

            elif highest_pending_severity == 7:
                if highest_active_ad_priority_level >= 2: 
                    should_run = True 
                    must_be_maintained = True 
                
            elif highest_pending_severity == 8:
                if highest_active_ad_priority_level >= 3: # 3 (High)
                    should_run = True 
                    must_be_maintained = True 
            
            # Note: If severity is 9 or 10, should_run stays False,
            # and the train is (correctly) not added to the schedule.

            if should_run:
                operating_trains.append(train)
                if must_be_maintained and active_ad_details:
                    ad_priority_str_val = active_ad_details.get('priority','N/A')
                    ad_priority_str_text = priority_text_map_backend.get(ad_priority_str_val, 'N/A')
                    
                    conflict_msg = (
                        f"train no {train.get('train_number', 'N/A')} is running now with ad priority:{ad_priority_str_text} ({ad_priority_str_val}), "
                        f"with maintenance level:{highest_pending_severity}"
                    )
                    conflicts_found.append(conflict_msg)

        # --- Time Table Generation ---
        
        timetable = []
        calculated_frequency = 0 # This will be the value we return
        if operating_trains:
            
            # 1. Calculate the ideal frequency
            # Use 120 (the assumed cycle time)
            calculated_frequency = round(120 / len(operating_trains), 2)
            
            # This check now ensures we don't loop if frequency is 0.0
            if calculated_frequency > 0:
                start_time = datetime.strptime("05:00", "%H:%M")
                end_time = datetime.strptime("23:00", "%H:%M")
                current_time = start_time
                train_index = 0
                
                max_iterations = 1000 
                iterations = 0
                
                while current_time < end_time and iterations < max_iterations:
                    train_on_duty = operating_trains[train_index]
                    timetable.append({
                        "time": current_time.strftime('%H:%M'),
                        "train_number": train_on_duty.get('train_number', 'N/A'),
                        "train_id": train_on_duty.get('train_id', 'N/A')
                    })
                    
                    # 3. Use the correct ideal frequency
                    current_time += timedelta(minutes=calculated_frequency) 
                    train_index = (train_index + 1) % len(operating_trains)
                    iterations += 1
                
                if iterations >= max_iterations: print("Warning: Schedule generation hit max iterations limit.")

        return jsonify({
            "schedule": timetable,
            "conflicts": conflicts_found, 
            "frequency": calculated_frequency # This value is now the "ideal" frequency
        })
    except Exception as e:
        print(f"Error generating schedule: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate schedule: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)