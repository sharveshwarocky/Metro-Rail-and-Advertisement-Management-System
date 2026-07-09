# Metro-Rail-and-Advertisement-Management-System



## About

An integrated database management system designed for metro railways to coordinate train operation scheduling, maintenance planning, and priority-based painted advertisement management. This system prevents scheduling conflicts, improves operational efficiency and safety, and maximizes advertising revenue to address the real-world needs of modern metro railway management.

## Problem Statement

Efficient metro train management demands the coordinated scheduling of operations, timely maintenance, and commercial advertisement handling. Real-world metro networks struggle to schedule maintenance within limited windows without disrupting services, while also attempting to manage priority-based painted advertisements on trains. This project aims to develop a unified system that handles train schedules, maintenance logs, and priority ads to prevent operational overlaps and optimize efficiency.

## Tech Stack

* **Frontend:** HTML, CSS, and JavaScript.
* **Backend:** PHP and Python.
* **Database:** PostgreSQL.

## Key Features

* **Suitability Scoring System:** Calculates a suitability score per train using factors such as operational status, safety, cleaning, mileage, and advertising contracts.

* **Daily Scheduling:** Generates daily train assignments—designating trains for Service, Standby, or Maintenance—based on the calculated suitability score.

* **Train & Ad Management:** Adds and tracks trains by mileage, fitness status, and stabling location, while managing priority-based painted advertisement campaigns linked to specific contract durations.

* **Maintenance & Cleaning Logs:** Records and assigns priority-level maintenance jobs to certified admins within defined windows, preventing conflicts with painted ads. Logs cleaning activities and updates status per train.

* **Admin Management & Reporting:** Manages operators, roles, and skill sets for task assignment. Provides dashboards to view daily assignments, maintenance summaries, and ad contract impacts through a user-friendly interface.


## System Scope & Limitations

* **Optimization Window:** Optimizes train assignments for one day at a time; it does not support long-term predictive scheduling.

* **Tracking Constraints:** The system does not track live train locations or handle immediate, real-time changes mid-day.

* **Data Dependency:** It relies on accurate, manual input from admins for mileage, maintenance, and cleaning to generate daily plans; wrong or delayed inputs can skew suitability scores.

* **Scoring Simplification:** The suitability score uses weighted assumptions and may not capture unexpected nuances like passenger load, weather conditions, or sudden delays.

## Contributors

* Minishree Mahadevan (2024115004)
* Iniya Srinivasan (2024115008)
* Sharveshwar Shankar (2024115002)
