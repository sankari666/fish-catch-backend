import os
import pandas as pd

from flask import Flask, jsonify, request
from flask_cors import CORS

from db import get_cursor


app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# HOME / HEALTH CHECK
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "Fish Catch Backend is running"
    })


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard", methods=["GET"])
def dashboard():
    cursor = None

    try:
        cursor = get_cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM fish_data
        """)
        total_records = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(DISTINCT fish_name) AS total_species
            FROM fish_data
        """)
        total_species = cursor.fetchone()["total_species"]

        cursor.execute("""
            SELECT COUNT(DISTINCT location) AS total_locations
            FROM fish_data
        """)
        total_locations = cursor.fetchone()["total_locations"]

        cursor.execute("""
            SELECT *
            FROM fish_data
            LIMIT 100
        """)
        data = cursor.fetchall()

        return jsonify({
            "total_records": total_records,
            "total_species": total_species,
            "total_locations": total_locations,
            "data": data
        })

    except Exception as e:
        print("Dashboard error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# RECOMMENDATION
# --------------------------------------------------

@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    cursor = None

    try:
        cursor = get_cursor(dictionary=True)

        if request.method == "POST":
            data = request.get_json() or {}
            fish_name = data.get("fish_name") or data.get("species")

            if fish_name:
                cursor.execute("""
                    SELECT *
                    FROM fish_data
                    WHERE fish_name = %s
                """, (fish_name,))
            else:
                cursor.execute("""
                    SELECT *
                    FROM fish_data
                    LIMIT 100
                """)

        else:
            fish_name = (
                request.args.get("fish_name")
                or request.args.get("species")
            )

            if fish_name:
                cursor.execute("""
                    SELECT *
                    FROM fish_data
                    WHERE fish_name = %s
                """, (fish_name,))
            else:
                cursor.execute("""
                    SELECT *
                    FROM fish_data
                    LIMIT 100
                """)

        results = cursor.fetchall()

        return jsonify(results)

    except Exception as e:
        print("Recommendation error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# TREND
# --------------------------------------------------

@app.route("/trend", methods=["GET"])
def trend():
    cursor = None

    try:
        cursor = get_cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                fish_name,
                location,
                latitude,
                longitude,
                depth,
                temperature,
                date
            FROM fish_data
            ORDER BY date
        """)

        data = cursor.fetchall()

        return jsonify(data)

    except Exception as e:
        print("Trend error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# ANALYZE FISH
# --------------------------------------------------

@app.route("/analyze-fish", methods=["POST"])
def analyze_fish():
    try:
        if "file" not in request.files:
            return jsonify({
                "error": "No file uploaded"
            }), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "error": "No file selected"
            }), 400

        df = pd.read_csv(file)

        df = df.where(pd.notnull(df), None)

        return jsonify({
            "success": True,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records")
        })

    except Exception as e:
        print("Analyze fish error:", e)
        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# SEARCH FISH
# --------------------------------------------------

@app.route("/search/fish", methods=["GET"])
def search_fish():
    cursor = None

    try:
        fish_name = request.args.get("fish", "").strip()

        cursor = get_cursor(dictionary=True)

        if not fish_name:
            return jsonify({
                "error": "Please provide fish name"
            }), 400

        cursor.execute("""
            SELECT *
            FROM fish_data
            WHERE fish_name LIKE %s
        """, (f"%{fish_name}%",))

        results = cursor.fetchall()

        return jsonify(results)

    except Exception as e:
        print("Fish search error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# SEARCH LOCATION
# --------------------------------------------------

@app.route("/search/location", methods=["GET"])
def search_location():
    cursor = None

    try:
        location = request.args.get("location", "").strip()

        cursor = get_cursor(dictionary=True)

        if not location:
            return jsonify({
                "error": "Please provide location"
            }), 400

        cursor.execute("""
            SELECT *
            FROM fish_data
            WHERE location LIKE %s
        """, (f"%{location}%",))

        results = cursor.fetchall()

        return jsonify(results)

    except Exception as e:
        print("Location search error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# SEARCH DATA
# --------------------------------------------------

@app.route("/search/data", methods=["GET"])
def search_data():
    cursor = None

    try:
        search = request.args.get("search", "").strip()

        cursor = get_cursor(dictionary=True)

        if not search:
            cursor.execute("""
                SELECT *
                FROM fish_data
                LIMIT 100
            """)
        else:
            cursor.execute("""
                SELECT *
                FROM fish_data
                WHERE fish_name LIKE %s
                   OR location LIKE %s
            """, (
                f"%{search}%",
                f"%{search}%"
            ))

        results = cursor.fetchall()

        return jsonify(results)

    except Exception as e:
        print("Data search error:", e)
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )