import os
import random
import pandas as pd
import mysql.connector
from flask import Flask, jsonify
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from db import db, get_cursor

app = Flask(__name__)
CORS(app)

# ==============================
# FOLDERS
# ==============================
UPLOAD_FOLDER = "uploads"
CLEAN_FOLDER = "cleaned"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEAN_FOLDER, exist_ok=True)

# ==============================
# MOCK FISH DATABASE (AI Simulation)
# ==============================
FISH_DATABASE = [
    {
        "fish_name": "Tuna",
        "location": "Indian Ocean",
        "latitude": 8.7832,
        "longitude": 73.0000,
        "depth_m": 200,
        "temperature_c": 22
    },
    {
        "fish_name": "Salmon",
        "location": "North Atlantic",
        "latitude": 45.0000,
        "longitude": -30.0000,
        "depth_m": 100,
        "temperature_c": 12
    },
    {
        "fish_name": "Clownfish",
        "location": "Pacific Ocean",
        "latitude": -15.0000,
        "longitude": 145.0000,
        "depth_m": 20,
        "temperature_c": 26
    }
]

# ==============================
# CAPTURE & ANALYZE FISH IMAGE
# ==============================
@app.route("/analyze-fish", methods=["POST"])
def analyze_fish():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image uploaded"}), 400

    image = request.files["image"]
    filename = image.filename.lower()
    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(image_path)

    # 🔥 Smarter Prediction Based on Filename
    if "mackerel" in filename:
        predicted_name = "Mackerel"
    elif "tuna" in filename:
        predicted_name = "Tuna"
    elif "salmon" in filename:
        predicted_name = "Salmon"
    elif "clown" in filename:
        predicted_name = "Clownfish"
    else:
        predicted_name = "Unknown"

    cursor = get_cursor(dictionary=True)
    cursor.execute("""
        SELECT fish_name, location, latitude, longitude, depth_m, temperature_c
        FROM fish_data
        WHERE LOWER(fish_name) = LOWER(%s)
        LIMIT 1
    """, (predicted_name,))

    data = cursor.fetchone()

    return jsonify({
        "success": True,
        "prediction": predicted_name,
        "details": data
    })

# ==============================
# DASHBOARD
# ==============================
@app.route("/dashboard")
def dashboard():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sivuselva@666",
        database="fishrepo"
    )

    cursor = conn.cursor(dictionary=True)

    # Total records
    cursor.execute("SELECT COUNT(*) as total_records FROM fish_data")
    total = cursor.fetchone()

    # Fish species counts
    cursor.execute("""
        SELECT fish_name, COUNT(*) as count
        FROM fish_data
        GROUP BY fish_name
    """)
    species = cursor.fetchall()

    # Location counts
    cursor.execute("""
        SELECT location, COUNT(*) as count
        FROM fish_data
        GROUP BY location
    """)
    locations = cursor.fetchall()

    conn.close()

    return jsonify({
        "total_records": total["total_records"],
        "species_data": species,
        "location_data": locations
    })
# ==============================
# RECOMMENDATION SYSTEM
# ==============================
@app.route("/recommend")
def recommend():

    location = request.args.get("location")
    month = request.args.get("month")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sivuselva@666",
        database="fishrepo"
    )
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT fish_name, location, temperature_c, depth_m
    FROM fish_data
    WHERE location=%s
    AND MONTH(date)=%s
    """

    cursor.execute(query,(location,month))

    rows = cursor.fetchall()

    return jsonify(rows)


# ==============================
# TREND ANALYSIS
# ==============================
@app.route("/trend")
def trend():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sivuselva@666",
        database="fishrepo"
    )

    cursor = conn.cursor()

    cursor.execute("""
    SELECT YEAR(date) as year, COUNT(*) as count
    FROM fish_data
    GROUP BY YEAR(date)
    ORDER BY YEAR(date)
    """)

    rows = cursor.fetchall()

    data = []

    for r in rows:
        data.append({
            "year": r[0],
            "count": r[1]
        })

    conn.close()

    return jsonify(data)

# ==============================
# UPLOAD + CLEAN CSV
# ==============================
@app.route("/upload", methods=["POST"])
def upload_csv():
    try:
        # ✅ Check file exists
        if "file" not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "message": "Empty filename"}), 400

        upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(upload_path)

        # ==============================
        # READ CSV (SAFE MODE)
        # ==============================
        try:
            df = pd.read_csv(
                upload_path,
                on_bad_lines="skip",   # 🔥 skip broken rows
                encoding="utf-8",
                skip_blank_lines=True
            )
        except Exception:
            return jsonify({
                "success": False,
                "message": "CSV parsing failed (invalid format)"
            }), 400

        if df.empty:
            return jsonify({
                "success": False,
                "message": "CSV is empty"
            }), 400

        # ==============================`1`
        # CLEAN COLUMN NAMES
        # ==============================
        df.columns = [col.strip().lower() for col in df.columns]

        rename_map = {
            "name": "fish_name",
            "fish": "fish_name",
            "lat": "latitude",
            "latitude": "latitude",
            "lon": "longitude",
            "lng": "longitude",
            "long": "longitude",
            "depth": "depth_m",
            "temp": "temperature_c",
            "temperature": "temperature_c"
}
        df.rename(columns=rename_map, inplace=True)

        # ==============================
        # CLEAN DATA VALUES
        # ==============================
        df = df.replace(["NA", "null", "unknown", "?", ""], None)

        # remove extra spaces
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # ==============================
        # CONVERT NUMERIC
        # ==============================
        numeric_cols = ["latitude", "longitude", "depth_m", "temperature_c"]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # ==============================
        # DROP INVALID ROWS (SAFE)
        # ==============================
        required_cols = ["fish_name", "latitude", "longitude"]
        existing_cols = [col for col in required_cols if col in df.columns]

        if not existing_cols:
            return jsonify({
                "success": False,
                "message": "Required columns missing (fish_name, latitude, longitude)"
            }), 400

        df = df.dropna(subset=existing_cols)

        if df.empty:
            return jsonify({
                "success": False,
                "message": "No valid data after cleaning"
            }), 400

        # ==============================
        # SAVE CLEAN FILE
        # ==============================
        cleaned_filename = "cleaned_" + file.filename
        cleaned_path = os.path.join(CLEAN_FOLDER, cleaned_filename)
        df.to_csv(cleaned_path, index=False)

        # ==============================
        # INSIGHTS
        # ==============================
        total_records = len(df)

        avg_depth = (
            round(df["depth_m"].mean(), 2)
            if "depth_m" in df.columns and not df["depth_m"].isna().all()
            else 0
        )

        avg_temp = (
            round(df["temperature_c"].mean(), 2)
            if "temperature_c" in df.columns and not df["temperature_c"].isna().all()
            else 0
        )

        unique_locations = (
            df["location"].nunique()
            if "location" in df.columns
            else 0
        )

        deepest_fish = None
        hottest_fish = None

        if "depth_m" in df.columns and not df["depth_m"].isna().all():
            deepest_fish = df.loc[df["depth_m"].idxmax()]["fish_name"]

        if "temperature_c" in df.columns and not df["temperature_c"].isna().all():
            hottest_fish = df.loc[df["temperature_c"].idxmax()]["fish_name"]

        # ==============================
        # CHART DATA
        # ==============================
        chart_columns = ["fish_name", "depth_m", "temperature_c"]
        available_columns = [col for col in chart_columns if col in df.columns]

        chart_df = df[available_columns].fillna(0)

        # ==============================
        # RESPONSE
        # ==============================
        return jsonify({
            "success": True,
            "file": cleaned_filename,
            "insights": {
                "total_records": total_records,
                "avg_depth": avg_depth,
                "avg_temp": avg_temp,
                "unique_locations": unique_locations,
                "deepest_fish": deepest_fish,
                "hottest_fish": hottest_fish
            },
            "chart_data": chart_df.to_dict(orient="records")
        })

    except Exception as e:
        print("ERROR:", str(e))  # 🔥 debug in terminal
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500


# ==============================
# DOWNLOAD CLEANED FILE
# ==============================
@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(CLEAN_FOLDER, filename)

    if not os.path.exists(path):
        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404

    return send_file(path, as_attachment=True)


# ==============================
# SEARCH ENDPOINTS
# ==============================
@app.route("/search/fish")
def search_fish():
    name = request.args.get("name")

    cursor = get_cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM fish_data
        WHERE LOWER(TRIM(fish_name)) LIKE LOWER(%s)
    """, (f"%{name.strip()}%",))

    return jsonify(cursor.fetchall())


@app.route("/search/location")
def search_location():
    location = request.args.get("location")

    cursor = get_cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM fish_data
        WHERE location LIKE %s
    """, (f"%{location}%",))

    return jsonify(cursor.fetchall())


@app.route("/search/data")
def search_data():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    cursor = get_cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM fish_data
        WHERE latitude BETWEEN %s AND %s
        AND longitude BETWEEN %s AND %s
    """, (
        lat - 0.5, lat + 0.5,
        lon - 0.5, lon + 0.5
    ))

    return jsonify(cursor.fetchall())


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(debug=True)