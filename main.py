import os
from datetime import datetime
from io import StringIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, make_response, flash
)
from flask_sqlalchemy import SQLAlchemy
import requests


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "dev-key")  

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


API_KEY = os.getenv("OPENWEATHER_API_KEY", "ab664813fee1e1d96ac7a8e3ed25c8a2")


class WeatherRecord(db.Model):
    __tablename__ = "weather_records"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(10), nullable=True)


    start_date = db.Column(db.String(20), nullable=True)
    end_date = db.Column(db.String(20), nullable=True)

    temperature = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(50), nullable=True)

   
    raw_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()



def validate_date(date_str: str | None) -> bool:
   
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def ow_icon_url(icon_code: str | None) -> str | None:
    if not icon_code:
        return None
    return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"



@app.route("/", methods=["GET", "POST"])
def home():
 
    weather_info = None
    forecast_info = None
    error = None

    if request.method == "POST":
        city = (request.form.get("city") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()

        if not city:
            error = "Please provide a city name."
        elif not (validate_date(start_date) and validate_date(end_date)):
            error = "Dates must be in YYYY-MM-DD format."
        else:
           
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            w_params = {"q": city, "appid": API_KEY, "units": "metric"}

            try:
                w_res = requests.get(weather_url, params=w_params, timeout=10)
                w_json = w_res.json()

              
                cod = int(w_json.get("cod", 0))
                if cod != 200:
                    error = w_json.get("message", "Unknown error").capitalize()
                else:
                    icon_code = (w_json.get("weather") or [{}])[0].get("icon")
                    desc = (w_json.get("weather") or [{}])[0].get("description", "")
                    weather_info = {
                        "city": w_json.get("name"),
                        "country": (w_json.get("sys") or {}).get("country"),
                        "temperature": round((w_json.get("main") or {}).get("temp", 0.0), 1),
                        "description": desc.capitalize(),
                        "icon": ow_icon_url(icon_code),
                    }

                  
                    record = WeatherRecord(
                        city=weather_info["city"],
                        country=weather_info["country"],
                        start_date=start_date or None,
                        end_date=end_date or None,
                        temperature=weather_info["temperature"],
                        description=weather_info["description"],
                        icon=icon_code,
                        raw_json=str(w_json)
                    )
                    db.session.add(record)
                    db.session.commit()
                    flash("Weather saved to history.", "success")

                    
                    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
                    f_params = {"q": city, "appid": API_KEY, "units": "metric"}
                    f_res = requests.get(forecast_url, params=f_params, timeout=10)
                    f_json = f_res.json()
                    if str(f_json.get("cod")) == "200":
                        forecast_info, seen_dates = [], set()
                        for entry in f_json.get("list", []):
                            dt_txt = entry.get("dt_txt", "")
                            date = dt_txt.split(" ")[0] if dt_txt else ""
                            if date and date not in seen_dates:
                                fc_icon = (entry.get("weather") or [{}])[0].get("icon")
                                fc_desc = (entry.get("weather") or [{}])[0].get("description", "")
                                forecast_info.append({
                                    "date": date,
                                    "temperature": round((entry.get("main") or {}).get("temp", 0.0), 1),
                                    "description": fc_desc.capitalize(),
                                    "icon": ow_icon_url(fc_icon),
                                })
                                seen_dates.add(date)

            except requests.exceptions.RequestException as e:
                error = f"Network error: {e}"

    return render_template(
        "w.html",
        weather=weather_info,
        forecast=forecast_info,
        error=error
    )

@app.route("/history", methods=["GET"])
def history():
   
    records = WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).all()
    return render_template("history.html", records=records)

@app.route("/update/<int:record_id>", methods=["GET", "POST"])
def update_record(record_id: int):
   
    record = WeatherRecord.query.get_or_404(record_id)

    if request.method == "POST":
        city = (request.form.get("city") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        temperature = request.form.get("temperature")
        description = (request.form.get("description") or "").strip()

        if not city:
            flash("City is required.", "error")
            return redirect(url_for("update_record", record_id=record_id))
        if not (validate_date(start_date) and validate_date(end_date)):
            flash("Dates must be in YYYY-MM-DD format.", "error")
            return redirect(url_for("update_record", record_id=record_id))

        try:
            record.city = city
            record.start_date = start_date or None
            record.end_date = end_date or None
            record.temperature = float(temperature) if temperature else record.temperature
            record.description = description or record.description
            db.session.commit()
            flash("Record updated.", "success")
            return redirect(url_for("history"))
        except Exception as e:
            db.session.rollback()
            flash(f"Update failed: {e}", "error")
            return redirect(url_for("update_record", record_id=record_id))

    return render_template("update.html", record=record)

@app.route("/delete/<int:record_id>", methods=["POST", "GET"])
def delete_record(record_id: int):
   
    record = WeatherRecord.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash("Record deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Delete failed: {e}", "error")
    return redirect(url_for("history"))



@app.route("/weather_by_coords")
def weather_by_coords():
  
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if int(data.get("cod", 0)) != 200:
            return jsonify({"error": data.get("message", "Unknown error")}), 400
        icon_code = (data.get("weather") or [{}])[0].get("icon")
        return jsonify({
            "city": data.get("name"),
            "country": (data.get("sys") or {}).get("country"),
            "temperature": round((data.get("main") or {}).get("temp", 0.0), 1),
            "description": ((data.get("weather") or [{}])[0].get("description") or "").capitalize(),
            "icon": ow_icon_url(icon_code)
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500




  


@app.route("/export/csv")
def export_csv():
  
    records = WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).all()
    csv_io = StringIO()
    csv_io.write("id,city,country,start_date,end_date,temperature,description,icon,created_at\n")
    for r in records:
        csv_io.write(
            f'{r.id},"{r.city or ""}","{r.country or ""}",'
            f'{r.start_date or ""},{r.end_date or ""},'
            f'{r.temperature if r.temperature is not None else ""},"{r.description or ""}",'
            f'{r.icon or ""},{r.created_at.isoformat()}\n'
        )
    resp = make_response(csv_io.getvalue())
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = "attachment; filename=weather_export.csv"
    return resp


if __name__ == "__main__":
  
    app.run(debug=True)
