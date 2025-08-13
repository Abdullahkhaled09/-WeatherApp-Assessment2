# Flask Weather App with Database CRUD – PMA Assessment 2

##  Project Overview
This is a **Python Flask** web application that:
- Fetches real-time weather data from the **OpenWeatherMap API**.
- Stores weather records in a **SQLite database**.
- Allows full **CRUD operations** (Create, Read, Update, Delete) on saved records.
- Includes optional features such as **data export (JSON/CSV)**, **5-day forecast**, and **current location detection**.

This project was built for **PMA Assessment 2**, extending the functionality from **Assessment 1** by adding **database persistence** and **record management**.

---

##  Tech Stack
- **Backend:** Python 3, Flask, SQLite (SQLAlchemy ORM)
- **Frontend:** HTML5, CSS (Bootstrap optional)
- **API:** OpenWeatherMap API
- **Tools:** Git, GitHub

---

##  Features

### **Mandatory (Assessment Requirements)**
 **Create** – Search for a city, fetch weather data, and store it in the database.  
 **Read** – View stored weather records in a history table.  
 **Update** – Edit stored records (city name, temperature, description).  
 **Delete** – Remove records from the database.  

### **Optional Enhancements that was implemented**
 **5-Day Forecast** – Displays upcoming weather after search.  
 **Current Location Detection** – Fetches weather for your geolocation.  
 **Data Export** – Download stored records in  CSV format.  

---

##  Project Structure
WeatherApp-Assessment2/
│
├── app.py # Main Flask application
├── weather.db # SQLite database (auto-created if missing)
├── requirements.txt # Python dependencies
├── README.md # Project documentation
│
├── templates/ # HTML templates (Jinja2)
│ ├── w.html # Main search page
│ ├── history.html # Weather history page
│ └── update.html # Update form page
##  How It Works (Step-by-Step Code Flow)

### **1. User Search (Create)**
- User enters a **city name** and optional **date range** on `w.html`.
- Flask route `/` (POST request) captures the input.
- Calls OpenWeatherMap API:
  
  url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
  response = requests.get(url)
  Parses JSON response and saves:

City

Country

Temperature

Description

Icon

Date range

Inserts into SQLite database via SQLAlchemy ORM.

2. View Records (Read)
/history route fetches all rows from the database

3. Edit Records (Update)
/update/<id> route fetches a single record.

Prefills a form with existing data.

User edits and submits = record is updated in the database.
4. Remove Records (Delete)
/delete/<id> deletes the matching record.
5. Export Data
/export/csv = Downloads CSV of all records.
6. Error Handling
If API returns an invalid city:
if data.get("cod") != 200:
    error = data.get("message", "Unknown error").capitalize()
If network or API issues occur, an error message is displayed.
