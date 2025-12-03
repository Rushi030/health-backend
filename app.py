#!/usr/bin/env python3
"""
Health Assistant Backend API
Flask application with SQLite database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import hashlib
import os

if not os.path.exists("health_assistant.db"):
    from db_manager import create_database
    create_database()




app = Flask(__name__)
CORS(app)

DATABASE = 'health_assistant.db'

# ============================================
#           DATABASE UTILITIES
# ============================================

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                age TEXT DEFAULT '',
                bio TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                doctor TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        ''')
        
        # Medications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                frequency TEXT NOT NULL,
                duration INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        ''')
        
        # Health records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE NOT NULL,
                blood_group TEXT,
                height REAL,
                weight REAL,
                emergency_name TEXT,
                emergency_relation TEXT,
                emergency_phone TEXT,
                medical_conditions TEXT,
                allergies TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        ''')
        
        # Activity logs table (for tracking user actions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        ''')
        
        print("✅ Database initialized successfully!")
        print(f"📊 Database file: {DATABASE}")

# ============================================
#           AUTHENTICATION ROUTES
# ============================================

@app.route("/signup", methods=["POST"])
def signup():
    """Register a new user"""
    try:
        data = request.json
        
        # Validation
        if not data.get("name") or not data.get("email") or not data.get("password"):
            return jsonify({"status": "error", "msg": "All fields are required"})
        
        # Validate email format
        email = data["email"].strip().lower()
        if "@" not in email or "." not in email.split("@")[1]:
            return jsonify({"status": "error", "msg": "Invalid email format"})
        
        # Password strength check
        if len(data["password"]) < 6:
            return jsonify({"status": "error", "msg": "Password must be at least 6 characters"})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
            if cursor.fetchone():
                return jsonify({"status": "error", "msg": "Email already registered"})
            
            # Hash password and insert user
            hashed_password = hash_password(data["password"])
            cursor.execute('''
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            ''', (data["name"].strip(), email, hashed_password))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action, details)
                VALUES (?, ?, ?)
            ''', (email, "signup", f"New user registered: {data['name']}"))
            
            return jsonify({
                "status": "success", 
                "msg": "Account created successfully! Please login."
            })
            
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and return user data"""
    try:
        data = request.json
        
        if not data.get("email") or not data.get("password"):
            return jsonify({"status": "error", "msg": "Email and password required"})
        
        email = data["email"].strip().lower()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute('''
                SELECT id, name, email, age, bio, password
                FROM users 
                WHERE LOWER(email) = ?
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"status": "error", "msg": "Email not found"})
            
            # Verify password
            hashed_password = hash_password(data["password"])
            if user["password"] != hashed_password:
                return jsonify({"status": "error", "msg": "Invalid password"})
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action)
                VALUES (?, ?)
            ''', (email, "login"))
            
            # Return user data (without password)
            user_data = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "age": user["age"],
                "bio": user["bio"]
            }
            
            return jsonify({"status": "success", "user": user_data})
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

# ============================================
#           PROFILE ROUTES
# ============================================

@app.route("/profile/save", methods=["POST"])
def save_profile():
    """Update user profile information"""
    try:
        data = request.json
        
        if not data.get("email"):
            return jsonify({"status": "error", "msg": "Email required"})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET name = ?, age = ?, bio = ?
                WHERE LOWER(email) = ?
            ''', (data.get("name", ""), data.get("age", ""), 
                  data.get("bio", ""), data["email"].lower()))
            
            if cursor.rowcount == 0:
                return jsonify({"status": "error", "msg": "User not found"})
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action)
                VALUES (?, ?)
            ''', (data["email"].lower(), "profile_update"))
            
            return jsonify({"status": "success", "msg": "Profile updated successfully"})
            
    except Exception as e:
        print(f"❌ Profile save error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

# ============================================
#           APPOINTMENT ROUTES
# ============================================

@app.route("/appointment/add", methods=["POST"])
def add_appointment():
    """Book a new appointment"""
    try:
        data = request.json
        
        required = ["email", "doctor", "date", "time"]
        if not all(data.get(field) for field in required):
            return jsonify({"status": "error", "msg": "All fields required"})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if time slot is available
            cursor.execute('''
                SELECT id FROM appointments 
                WHERE doctor = ? AND date = ? AND time = ?
            ''', (data["doctor"], data["date"], data["time"]))
            
            if cursor.fetchone():
                return jsonify({
                    "status": "error", 
                    "msg": "This time slot is already booked. Please choose another time."
                })
            
            # Insert appointment
            cursor.execute('''
                INSERT INTO appointments (user_email, doctor, date, time)
                VALUES (?, ?, ?, ?)
            ''', (data["email"].lower(), data["doctor"], data["date"], data["time"]))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action, details)
                VALUES (?, ?, ?)
            ''', (data["email"].lower(), "appointment_booked", 
                  f"{data['doctor']} on {data['date']} at {data['time']}"))
            
            return jsonify({
                "status": "success", 
                "msg": "Appointment booked successfully!"
            })
            
    except Exception as e:
        print(f"❌ Appointment add error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

@app.route("/appointment/get", methods=["POST"])
def get_appointments():
    """Get all appointments for a user"""
    try:
        data = request.json
        
        if not data.get("email"):
            return jsonify([])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, doctor, date, time, booked_at
                FROM appointments 
                WHERE LOWER(user_email) = ?
                ORDER BY date DESC, time DESC
            ''', (data["email"].lower(),))
            
            appointments = [dict(row) for row in cursor.fetchall()]
            return jsonify(appointments)
            
    except Exception as e:
        print(f"❌ Get appointments error: {e}")
        return jsonify([])

@app.route("/appointment/delete/<int:appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id):
    """Cancel an appointment"""
    try:
        data = request.json
        email = data.get("email", "").lower()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM appointments 
                WHERE id = ? AND LOWER(user_email) = ?
            ''', (appointment_id, email))
            
            if cursor.rowcount == 0:
                return jsonify({"status": "error", "msg": "Appointment not found"})
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action, details)
                VALUES (?, ?, ?)
            ''', (email, "appointment_cancelled", f"Appointment ID: {appointment_id}"))
            
            return jsonify({"status": "success", "msg": "Appointment cancelled"})
            
    except Exception as e:
        print(f"❌ Delete appointment error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

# ============================================
#           MEDICATION ROUTES
# ============================================

@app.route("/medication/add", methods=["POST"])
def add_medication():
    """Add a new medication reminder"""
    try:
        data = request.json
        
        required = ["email", "name", "dosage", "frequency", "duration"]
        if not all(data.get(field) for field in required):
            return jsonify({"status": "error", "msg": "All fields required"})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO medications (user_email, name, dosage, frequency, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (data["email"].lower(), data["name"], data["dosage"], 
                  data["frequency"], data["duration"]))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_logs (user_email, action, details)
                VALUES (?, ?, ?)
            ''', (data["email"].lower(), "medication_added", 
                  f"{data['name']} - {data['dosage']}"))
            
            return jsonify({
                "status": "success", 
                "msg": "Medication added successfully!"
            })
            
    except Exception as e:
        print(f"❌ Medication add error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

@app.route("/medication/get", methods=["POST"])
def get_medications():
    """Get all medications for a user"""
    try:
        data = request.json
        
        if not data.get("email"):
            return jsonify([])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, dosage, frequency, duration, created_at
                FROM medications 
                WHERE LOWER(user_email) = ?
                ORDER BY created_at DESC
            ''', (data["email"].lower(),))
            
            medications = [dict(row) for row in cursor.fetchall()]
            return jsonify(medications)
            
    except Exception as e:
        print(f"❌ Get medications error: {e}")
        return jsonify([])

@app.route("/medication/delete/<int:medication_id>", methods=["DELETE"])
def delete_medication(medication_id):
    """Delete a medication"""
    try:
        data = request.json
        email = data.get("email", "").lower()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM medications 
                WHERE id = ? AND LOWER(user_email) = ?
            ''', (medication_id, email))
            
            if cursor.rowcount == 0:
                return jsonify({"status": "error", "msg": "Medication not found"})
            
            return jsonify({"status": "success", "msg": "Medication deleted"})
            
    except Exception as e:
        print(f"❌ Delete medication error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

# ============================================
#           HEALTH RECORDS ROUTES
# ============================================

@app.route("/health_records/save", methods=["POST"])
def save_health_records():
    """Save or update health records"""
    try:
        data = request.json
        
        if not data.get("email"):
            return jsonify({"status": "error", "msg": "Email required"})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute('''
                SELECT id FROM health_records WHERE LOWER(user_email) = ?
            ''', (data["email"].lower(),))
            
            if cursor.fetchone():
                # Update existing record
                cursor.execute('''
                    UPDATE health_records 
                    SET blood_group = ?, height = ?, weight = ?,
                        emergency_name = ?, emergency_relation = ?, emergency_phone = ?,
                        medical_conditions = ?, allergies = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE LOWER(user_email) = ?
                ''', (data.get("blood_group"), data.get("height"), data.get("weight"),
                      data.get("emergency_name"), data.get("emergency_relation"), 
                      data.get("emergency_phone"), data.get("medical_conditions"),
                      data.get("allergies"), data["email"].lower()))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO health_records 
                    (user_email, blood_group, height, weight, emergency_name, 
                     emergency_relation, emergency_phone, medical_conditions, allergies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data["email"].lower(), data.get("blood_group"), data.get("height"),
                      data.get("weight"), data.get("emergency_name"), 
                      data.get("emergency_relation"), data.get("emergency_phone"),
                      data.get("medical_conditions"), data.get("allergies")))
            
            return jsonify({"status": "success", "msg": "Health records saved"})
            
    except Exception as e:
        print(f"❌ Health records save error: {e}")
        return jsonify({"status": "error", "msg": "Server error occurred"})

@app.route("/health_records/get", methods=["POST"])
def get_health_records():
    """Get health records for a user"""
    try:
        data = request.json
        
        if not data.get("email"):
            return jsonify({})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM health_records 
                WHERE LOWER(user_email) = ?
            ''', (data["email"].lower(),))
            
            record = cursor.fetchone()
            return jsonify(dict(record) if record else {})
            
    except Exception as e:
        print(f"❌ Get health records error: {e}")
        return jsonify({})

# ============================================
#           CHATBOT ROUTE
# ============================================

@app.route("/chat", methods=["POST"])
def chat():
    """AI Health Assistant chatbot"""
    try:
        data = request.json
        q = data.get("question", "").lower()

        responses = {
            "fever": "🌡️ For fever: Drink plenty of water, rest well, and take paracetamol 500mg if needed. If fever persists above 102°F or lasts more than 3 days, consult a doctor immediately.",
            
            "headache": "💆 For headache: Rest in a quiet, dark room, stay hydrated, reduce screen time, and try a cold compress on your forehead. If severe or persistent, consult a doctor.",
            
            "cold": "🤧 For cold: Try steam inhalation, drink warm fluids like herbal tea or honey-lemon water, get adequate rest, and maintain good hygiene. Usually resolves in 7-10 days.",
            
            "cough": "😷 For cough: Stay hydrated, use honey (for adults), avoid irritants like smoke, and try warm liquids with ginger. See a doctor if it persists beyond 3 weeks or worsens.",
            
            "stomach": "🤢 For stomach issues: Eat bland foods (BRAT diet: Bananas, Rice, Applesauce, Toast), stay hydrated with electrolyte solutions, avoid spicy/fatty foods. If severe pain, vomiting blood, or high fever present, seek immediate medical attention.",
            
            "pain": "💊 For general pain: Rest the affected area, apply ice for acute injuries or heat for muscle tension, consider over-the-counter pain relief (as directed). Persistent or severe pain requires medical evaluation.",
            
            "stress": "🧘 For stress management: Practice deep breathing exercises, engage in regular physical activity, maintain 7-8 hours of sleep, talk to someone you trust. Consider meditation, yoga, or professional counseling.",
            
            "sleep": "😴 For better sleep: Maintain consistent sleep schedule (same bedtime/wake time), avoid screens 1 hour before bed, keep room cool (60-67°F) and dark, avoid caffeine after 2 PM, try relaxation techniques.",
            
            "diet": "🥗 For healthy diet: Include 5 servings of fruits and vegetables daily, choose whole grains over refined, eat lean proteins (fish, chicken, legumes), limit processed foods and added sugars. Drink 8 glasses of water daily.",
            
            "exercise": "🏃 For exercise: Aim for 150 minutes of moderate activity or 75 minutes of vigorous activity weekly. Mix cardio (walking, cycling) and strength training. Start slowly, warm up properly, and listen to your body.",
            
            "diabetes": "🩺 For diabetes management: Monitor blood sugar regularly, follow prescribed medication, eat balanced meals with controlled carbs, exercise regularly, maintain healthy weight. Regular check-ups are crucial.",
            
            "blood pressure": "❤️ For blood pressure: Reduce sodium intake, eat potassium-rich foods (bananas, spinach), exercise regularly, maintain healthy weight, limit alcohol, manage stress. Monitor regularly and follow doctor's advice.",
            
            "weight": "⚖️ For healthy weight: Create moderate calorie deficit (500 cal/day for 1 lb/week loss), eat protein-rich foods, increase fiber intake, stay hydrated, get adequate sleep, combine diet with exercise.",
            
            "anxiety": "😰 For anxiety: Practice mindfulness and deep breathing, maintain regular exercise routine, limit caffeine and alcohol, establish healthy sleep habits, consider talking to a mental health professional."
        }

        reply = None
        for keyword, response in responses.items():
            if keyword in q:
                reply = response
                break

        if not reply:
            if any(word in q for word in ["hello", "hi", "hey"]):
                reply = "👋 Hello! I'm your AI Health Assistant. I can help you with questions about common health issues like fever, headache, cold, diet, exercise, stress, sleep, and more. What would you like to know?"
            elif "appointment" in q:
                reply = "📅 To book an appointment, please go to the 'Appointments' tab where you can select a doctor, date, and time slot. Our doctors are available from 9 AM to 5 PM, Monday to Saturday."
            elif "medication" in q or "medicine" in q:
                reply = "💊 For medication reminders, visit the 'Medications' tab where you can add your prescriptions and set up automatic reminders. Never miss a dose!"
            else:
                reply = "🤔 I'm not sure about that specific question. For personalized medical advice, please consult a qualified healthcare professional. You can also book an appointment with our doctors through the Appointments tab. Try asking about: fever, headache, cold, diet, exercise, stress, or sleep."

        return jsonify({"reply": reply})
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({
            "reply": "😓 Sorry, I encountered an error. Please try again or contact support if the issue persists."
        })

# ============================================
#           ADMIN & UTILITY ROUTES
# ============================================

@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    """Get database statistics"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # User count
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()["count"]
            
            # Appointment count
            cursor.execute("SELECT COUNT(*) as count FROM appointments")
            appointment_count = cursor.fetchone()["count"]
            
            # Medication count
            cursor.execute("SELECT COUNT(*) as count FROM medications")
            medication_count = cursor.fetchone()["count"]
            
            # Recent activity
            cursor.execute('''
                SELECT action, COUNT(*) as count 
                FROM activity_logs 
                WHERE date(timestamp) = date('now')
                GROUP BY action
            ''')
            today_activity = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                "users": user_count,
                "appointments": appointment_count,
                "medications": medication_count,
                "today_activity": today_activity
            })
            
    except Exception as e:
        print(f"❌ Admin stats error: {e}")
        return jsonify({"error": "Failed to fetch statistics"})

@app.route("/health", methods=["GET"])
def health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        
        return jsonify({
            "status": "healthy",
            "message": "Health Assistant API is running",
            "database": "connected",
            "users": user_count,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500
# ============================================
#           ADMIN SPECIFIC ROUTES (ADD THIS)
# ============================================

@app.route("/admin/all_appointments", methods=["POST"])
def admin_all_appointments():
    """Get ALL appointments for the doctor view"""
    try:
        # In a real app, verify admin session here
        with get_db() as conn:
            cursor = conn.cursor()
            # Join with users to get the Patient Name
            cursor.execute('''
                SELECT a.id, u.name as patient_name, u.age, a.doctor, a.date, a.time, a.user_email
                FROM appointments a
                JOIN users u ON a.user_email = u.email
                ORDER BY a.date DESC
            ''')
            appointments = [dict(row) for row in cursor.fetchall()]
            return jsonify(appointments)
    except Exception as e:
        return jsonify([])

@app.route("/admin/all_medications", methods=["POST"])
def admin_all_medications():
    """Get ALL medications for all users"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.id, u.name as patient_name, m.name as med_name, 
                       m.dosage, m.frequency, m.duration, m.user_email
                FROM medications m
                JOIN users u ON m.user_email = u.email
                ORDER BY m.created_at DESC
            ''')
            medications = [dict(row) for row in cursor.fetchall()]
            return jsonify(medications)
    except Exception as e:
        return jsonify([])

@app.route("/admin/all_records", methods=["POST"])
def admin_all_records():
    """Get ALL health records"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT h.*, u.name as patient_name, u.age
                FROM health_records h
                JOIN users u ON h.user_email = u.email
            ''')
            records = [dict(row) for row in cursor.fetchall()]
            return jsonify(records)
    except Exception as e:
        return jsonify([])
    
# ---------------------------
# ADMIN APPOINTMENT ACTIONS
# ---------------------------

@app.route("/admin/appointment/complete", methods=["POST"])
def admin_complete_appointment():
    try:
        data = request.json
        appt_id = data.get("id")

        if not appt_id:
            return jsonify({"status": "error", "msg": "Missing appointment ID"})

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))

            if cursor.rowcount == 0:
                return jsonify({"status": "error", "msg": "Appointment not found"})

        return jsonify({"status": "success", "msg": "Appointment marked as completed"})
    except Exception as e:
        print("❌ Complete appointment error:", e)
        return jsonify({"status": "error", "msg": "Server error"})


@app.route("/admin/appointment/delete", methods=["POST"])
def admin_delete_appointment():
    try:
        data = request.json
        appt_id = data.get("id")

        if not appt_id:
            return jsonify({"status": "error", "msg": "Missing appointment ID"})

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))

            if cursor.rowcount == 0:
                return jsonify({"status": "error", "msg": "Appointment not found"})

        return jsonify({"status": "success", "msg": "Appointment deleted"})
    except Exception as e:
        print("❌ Delete appointment error:", e)
        return jsonify({"status": "error", "msg": "Server error"})

# ============================================
#           MAIN
# ============================================
# (new admin routes here)
if __name__ == "__main__":
    # Initialize database
    init_db()
    
    print("\n" + "=" * 70)
    print("🏥 HEALTH ASSISTANT API SERVER")
    print("=" * 70)
    print(f"✅ Server running on: http://127.0.0.1:5000")
    print(f"✅ Database: {DATABASE}")
    print(f"✅ CORS enabled for frontend access")
    print(f"✅ All endpoints ready:")
    print(f"   • Authentication: /signup, /login")
    print(f"   • Profile: /profile/save")
    print(f"   • Appointments: /appointment/add, /appointment/get")
    print(f"   • Medications: /medication/add, /medication/get")
    print(f"   • Health Records: /health_records/save, /health_records/get")
    print(f"   • Chatbot: /chat")
    print(f"   • Admin: /admin/stats")
    print(f"   • Health Check: /health")
    print("=" * 70 + "\n")
    
    # Run Flask app


    app.run(debug=True, host="127.0.0.1", port=5000)




