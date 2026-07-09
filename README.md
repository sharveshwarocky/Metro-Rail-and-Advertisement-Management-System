# Metro-Rail-and-Advertisement-Management-System


Here is a complete, highly detailed `README.md` file designed to make your repository look professional, showcase your technical logic to recruiters, and provide foolproof instructions for anyone running the code.

You can copy and paste this directly into your GitHub repository!

---

# 🚇 Metro Rail Management System

## 📖 Overview

The **Metro Rail Management System** is a full-stack web application designed to streamline daily metro operations. It acts as an integrated hub to coordinate train schedules, track maintenance logs, and manage commercial advertisement campaigns.

The standout feature of this system is its **Automated Scheduling Algorithm**. It dynamically generates base depot schedules by evaluating a complex decision matrix: balancing the severity of a train's maintenance issues against the priority level of its active advertising contracts. This ensures maximum operational efficiency and revenue without compromising safety.

---

## ✨ Key Features

* **Dual-Backend Architecture:** * `app.py`: A robust, production-ready backend utilizing a **PostgreSQL** database.
* `appy.py`: A lightweight, zero-setup backend that uses **local CSV files** for seamless testing and portability.


* **Dynamic Decision Matrix (Scheduling Algorithm):** Automatically determines if a train is fit for service based on:
* **Low/Medium Issues (Severity 1-6):** Cleared for normal operation.
* **Severe Issues (Severity 7):** Grounded, *unless* the train carries a Medium or High priority ad (Priority $\ge$ 2).
* **Critical Issues (Severity 8):** Grounded, *unless* the train carries a High priority ad (Priority = 3).
* **Fatal Issues (Severity 9-10):** Grounded immediately, regardless of contracts.


* **Automated Conflict Logging:** Flags and alerts administrators to "High Conflicts" when a damaged train is forced into service to fulfill high-priority ad contracts.
* **Interactive Admin Dashboard:** A responsive, Single Page Application (SPA) built with Tailwind CSS. Features modal-driven forms for CRUD operations on trains, maintenance records, and ad campaigns.
* **Smart Status Management:** Automatically updates a train's master status to `In-Maintenance` when high-severity issues are logged, and restores it to `Available` once resolved.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, Vanilla JavaScript, Tailwind CSS (via CDN)
* **Backend:** Python, Flask
* **Database:** PostgreSQL (Primary), Local CSV (Fallback)
* **API:** RESTful JSON endpoints

---

## 🚀 Installation & Setup Guide

### Prerequisites

1. Ensure you have **Python 3.8+** installed on your machine.
2. Install the required Python libraries by running:
```bash
pip install flask psycopg2

```



### Option A: Running with PostgreSQL (Production Environment)

*Recommended for full database functionality.*

1. Install and start your local PostgreSQL server.
2. Create a new database named `metro_db`.
3. Open `app.py` and locate the Database Configuration section at the top. Update the `DB_PASS` variable with your local Postgres password:
```python
DB_HOST = "localhost"
DB_NAME = "metro_db"
DB_USER = "postgres"
DB_PASS = "Your_Password_Here" # <-- Update this
DB_PORT = "5432"

```


4. Run the application:
```bash
python app.py

```


5. The tables will be automatically created upon the first successful data entry.

### Option B: Running with Local CSV (Zero-Setup Environment)

*Recommended for quick testing without installing PostgreSQL.*

1. Ensure `appy.py` is in the same directory as your `templates/index.html` file.
2. Run the application:
```bash
python appy.py

```


3. The system will automatically create a `metro_data` folder containing `trains.csv`, `maintenance.csv`, and `advertisements.csv` to act as your database.

---

## 💻 How to Use the System (Showcase Guide)

Once the app is running, open your browser and navigate to `http://localhost:5000`.

### 1. Populate the Fleet (Trains Tab)

* Navigate to the **Trains** section.
* Click **Add New Train** to register a few trains (e.g., Train 101, Train 102) with their home locations.

### 2. Add Advertising Contracts (Advertisements Tab)

* Navigate to the **Advertisements** section.
* Assign ad contracts to your trains. Ensure you assign different priority levels: `1 (Low)`, `2 (Medium)`, and `3 (High)`.

### 3. Log Maintenance Issues (Maintenance Tab)

* Navigate to the **Maintenance** section.
* Log issues with varying severities (1 through 10) for your trains.
* *Note:* Notice how logging an issue with a severity of 7 or higher automatically changes that train's status on the Dashboard to `In-Maintenance`.

### 4. Test the Algorithm (Schedule Tab)

* Navigate to the **Schedule** section and click **Generate**.
* **What to look for:**
* The system will automatically calculate the dispatch frequency based on available trains (`120 minutes / operating trains`).
* If a train has a severity 7 issue but carries a Priority 2 ad, it will be dispatched, and a **Yellow Conflict Warning** will appear on the screen detailing the risk.
* Trains with severity 9 or 10 will be completely excluded from the timetable.

### 5. View Train History

* Go back to the **Trains** tab and click the **History** button next to any train.
* A modal will pop up showing the comprehensive history of that specific train, pulling data from both the maintenance and advertisement tables.

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/trains` | Fetches all registered trains and their status. |
| `GET` | `/api/trains/<id>/history` | Fetches consolidated maintenance and ad history for a specific train. |
| `POST` | `/api/trains/add` | Registers a new train to the fleet. |
| `POST` | `/api/maintenance/add` | Logs a maintenance issue and triggers auto-status updates if severe. |
| `POST` | `/api/ads/add` | Creates a new priority-based advertisement contract. |
| `POST` | `/api/schedule/generate` | Executes the scheduling algorithm and returns the timetable, conflicts, and frequency. |
| `DELETE` | `/api/trains/delete/<id>` | Removes a train and cascades deletions to its records. |

---

## 🚧 System Limitations

* **Optimization Window:** Schedules are generated for one fixed daily cycle (05:00 to 23:00); it does not currently support multi-day predictive scheduling.
* **Manual Data Dependency:** The algorithm relies on admins accurately logging cleaning, maintenance, and ad contracts in real-time.
* **Static Lookup:** The suitability score uses fixed parameters and does not dynamically adjust for unexpected real-world delays (e.g., passenger load, weather conditions).

---

## Contributors

* Minishree Mahadevan (2024115004)
* Iniya Srinivasan (2024115008)
* Sharveshwar Shankar (2024115002)

Developed as part of the Information Technology curriculum at **Anna University**.
