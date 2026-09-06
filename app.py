import os
import random
import pandas as pd
import numpy as np
import tensorflow as tf

from PIL import Image
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from db import get_cursor, close_db


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

app.teardown_appcontext(close_db)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "uploads"
CLEAN_FOLDER = "cleaned"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEAN_FOLDER, exist_ok=True)


# ============================================================
# AI MODEL
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "fish_model.h5"
)

LABELS_PATH = os.path.join(
    BASE_DIR,
    "model",
    "labels.txt"
)

model = None
class_names = []


# Load trained model
try:

    if os.path.exists(MODEL_PATH):

        model = tf.keras.models.load_model(
            MODEL_PATH
        )

        print("Fish model loaded successfully")

    else:

        print(
            "WARNING: Model not found:",
            MODEL_PATH
        )

    if os.path.exists(LABELS_PATH):

        with open(
            LABELS_PATH,
            "r"
        ) as f:

            class_names = [
                line.strip()
                for line in f
                if line.strip()
            ]

        print(
            "Fish labels loaded:",
            class_names
        )

    else:

        print(
            "WARNING: labels.txt not found:",
            LABELS_PATH
        )

except Exception as e:

    print(
        "ERROR loading fish model:",
        str(e)
    )


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Fish Catch Repository API is running",
        "status": "success"
    })


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    cursor = get_cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT COUNT(*) AS total_records
        FROM fish_data
    """)

    total = cursor.fetchone()

    cursor.execute("""
        SELECT fish_name,
               COUNT(*) AS count
        FROM fish_data
        GROUP BY fish_name
        ORDER BY count DESC
    """)

    species = cursor.fetchall()

    cursor.execute("""
        SELECT location,
               COUNT(*) AS count
        FROM fish_data
        GROUP BY location
        ORDER BY count DESC
    """)

    locations = cursor.fetchall()

    return jsonify({

        "total_records":
            total["total_records"],

        "species_data":
            species,

        "location_data":
            locations

    })


# ============================================================
# SEARCH FISH DATA
# ============================================================

@app.route("/search")
def search():

    search_term = request.args.get(
        "search",
        ""
    ).strip()

    cursor = get_cursor(
        dictionary=True
    )

    if search_term:

        query = """
            SELECT *
            FROM fish_data
            WHERE fish_name LIKE %s
               OR location LIKE %s
        """

        search_value = f"%{search_term}%"

        cursor.execute(
            query,
            (
                search_value,
                search_value
            )
        )

    else:

        cursor.execute("""
            SELECT *
            FROM fish_data
        """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# RECOMMENDATION
# ============================================================

@app.route("/recommend")
def recommend():

    location = request.args.get(
        "location"
    )

    month = request.args.get(
        "month"
    )

    cursor = get_cursor(
        dictionary=True
    )

    if location and month:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE location = %s
              AND MONTH(date) = %s
        """

        cursor.execute(
            query,
            (
                location,
                month
            )
        )

    elif location:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE location = %s
        """

        cursor.execute(
            query,
            (location,)
        )

    elif month:

        query = """
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
            WHERE MONTH(date) = %s
        """

        cursor.execute(
            query,
            (month,)
        )

    else:

        cursor.execute("""
            SELECT fish_name,
                   location,
                   temperature_c,
                   depth_m
            FROM fish_data
        """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# TREND
# ============================================================

@app.route("/trend")
def trend():

    cursor = get_cursor()

    cursor.execute("""
        SELECT YEAR(date) AS year,
               COUNT(*) AS count
        FROM fish_data
        GROUP BY YEAR(date)
        ORDER BY YEAR(date)
    """)

    rows = cursor.fetchall()

    data = []

    for row in rows:

        data.append({

            "year": row[0],

            "count": row[1]

        })

    return jsonify(data)


# ============================================================
# GET ALL FISH DATA
# ============================================================

@app.route("/fish-data")
def fish_data():

    cursor = get_cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM fish_data
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# GET UNIQUE LOCATIONS
# ============================================================

@app.route("/locations")
def locations():

    cursor = get_cursor()

    cursor.execute("""
        SELECT DISTINCT location
        FROM fish_data
        WHERE location IS NOT NULL
          AND location != ''
        ORDER BY location
    """)

    rows = cursor.fetchall()

    locations_list = [
        row[0]
        for row in rows
    ]

    return jsonify(
        locations_list
    )


# ============================================================
# GET UNIQUE FISH SPECIES
# ============================================================

@app.route("/species")
def species():

    cursor = get_cursor()

    cursor.execute("""
        SELECT DISTINCT fish_name
        FROM fish_data
        WHERE fish_name IS NOT NULL
          AND fish_name != ''
        ORDER BY fish_name
    """)

    rows = cursor.fetchall()

    species_list = [
        row[0]
        for row in rows
    ]

    return jsonify(
        species_list
    )


# ============================================================
# DOWNLOAD CSV
# ============================================================

@app.route("/download/csv")
def download_csv():

    cursor = get_cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM fish_data
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows)

    file_path = os.path.join(
        CLEAN_FOLDER,
        "fish_data.csv"
    )

    df.to_csv(
        file_path,
        index=False
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="fish_data.csv"
    )


# ============================================================
# DOWNLOAD EXCEL
# ============================================================

@app.route("/download/excel")
def download_excel():

    cursor = get_cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM fish_data
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows)

    file_path = os.path.join(
        CLEAN_FOLDER,
        "fish_data.xlsx"
    )

    df.to_excel(
        file_path,
        index=False
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name="fish_data.xlsx"
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    username = data.get(
        "username"
    )

    password = data.get(
        "password"
    )

    if not username or not password:

        return jsonify({

            "success": False,

            "message":
                "Username and password are required"

        }), 400

    cursor = get_cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = %s
          AND password = %s
    """, (
        username,
        password
    ))

    user = cursor.fetchone()

    if user:

        return jsonify({

            "success": True,

            "message":
                "Login successful",

            "user": user

        })

    return jsonify({

        "success": False,

        "message":
            "Invalid username or password"

    }), 401


# ============================================================
# UPLOAD CSV
# ============================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    if "file" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No file uploaded"

        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({

            "success": False,

            "message":
                "No file selected"

        }), 400

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(file_path)

    try:

        df = pd.read_csv(
            file_path
        )

        df = df.where(
            pd.notnull(df),
            None
        )

        cursor = get_cursor()

        columns = list(
            df.columns
        )

        column_names = ", ".join(
            f"`{column}`"
            for column in columns
        )

        placeholders = ", ".join(
            ["%s"] * len(columns)
        )

        query = f"""
            INSERT INTO fish_data
            ({column_names})
            VALUES ({placeholders})
        """

        for _, row in df.iterrows():

            values = tuple(
                row[column]
                for column in columns
            )

            cursor.execute(
                query,
                values
            )

        cursor.connection.commit()

        return jsonify({

            "success": True,

            "message":
                "File uploaded successfully",

            "records_added":
                len(df)

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ============================================================
# SEARCH BY COORDINATES
# ============================================================

@app.route("/search/data")
def search_data():

    lat = request.args.get(
        "lat",
        type=float
    )

    lon = request.args.get(
        "lon",
        type=float
    )

    radius = request.args.get(
        "radius",
        type=float,
        default=10
    )

    if lat is None or lon is None:

        return jsonify({

            "success": False,

            "message":
                "Latitude and longitude are required"

        }), 400

    cursor = get_cursor(
        dictionary=True
    )

    query = """
        SELECT *,
        (
            6371 * ACOS(
                COS(RADIANS(%s))
                * COS(RADIANS(latitude))
                * COS(
                    RADIANS(longitude)
                    - RADIANS(%s)
                )
                + SIN(RADIANS(%s))
                * SIN(RADIANS(latitude))
            )
        ) AS distance_km

        FROM fish_data

        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL

        HAVING distance_km <= %s

        ORDER BY distance_km ASC
    """

    cursor.execute(
        query,
        (
            lat,
            lon,
            lat,
            radius
        )
    )

    rows = cursor.fetchall()

    return jsonify(rows)


# ============================================================
# CAPTURE & ANALYZE FISH
# ============================================================

@app.route(
    "/analyze-fish",
    methods=["POST"]
)
def analyze_fish():

    # Check model
    if model is None:

        return jsonify({

            "success": False,

            "message":
                "Fish model is not loaded"

        }), 500

    # Check labels
    if not class_names:

        return jsonify({

            "success": False,

            "message":
                "Fish labels are not loaded"

        }), 500

    # Check image
    if "image" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No image uploaded"

        }), 400

    file = request.files["image"]

    if file.filename == "":

        return jsonify({

            "success": False,

            "message":
                "No image selected"

        }), 400

    try:

        # ----------------------------------------------------
        # Open image
        # ----------------------------------------------------

        image = Image.open(
            file.stream
        ).convert("RGB")

        # ----------------------------------------------------
        # Resize
        # ----------------------------------------------------

        image = image.resize(
            (224, 224)
        )

        # ----------------------------------------------------
        # Convert to NumPy
        # ----------------------------------------------------

        image_array = np.array(
            image,
            dtype=np.float32
        )

        # Add batch dimension
        image_array = np.expand_dims(
            image_array,
            axis=0
        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        predictions = model.predict(
            image_array,
            verbose=0
        )

        predicted_index = int(
            np.argmax(
                predictions[0]
            )
        )

        confidence = float(
            predictions[0][
                predicted_index
            ]
        )

        # ----------------------------------------------------
        # Get predicted fish name
        # ----------------------------------------------------

        if predicted_index >= len(
            class_names
        ):

            return jsonify({

                "success": False,

                "message":
                    "Predicted class does not match labels"

            }), 500

        prediction = class_names[
            predicted_index
        ]

        # ----------------------------------------------------
        # Get environmental data
        # ----------------------------------------------------

        cursor = get_cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                location,
                latitude,
                longitude,
                depth_m,
                temperature_c
            FROM fish_data
            WHERE LOWER(fish_name)
                  = LOWER(%s)
            LIMIT 1
        """, (
            prediction,
        ))

        details = cursor.fetchone()

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "prediction":
                prediction,

            "confidence":
                round(
                    confidence * 100,
                    2
                ),

            "details":
                details

        })

    except Exception as e:

        print(
            "ANALYZE FISH ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )