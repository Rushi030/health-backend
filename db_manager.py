#!/usr/bin/env python3
"""
Database Manager for Health Assistant
Manage, view, and maintain the SQLite database
"""

import sqlite3
from datetime import datetime
import hashlib

DATABASE = 'health_assistant.db'

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_database():
    """Create fresh database with all tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\n🔨 Creating database tables...\n")
    
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
    print("✅ Users table created")
    
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
    print("✅ Appointments table created")
    
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
    print("✅ Medications table created")
    
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
    print("✅ Health records table created")
    
    # Activity logs table
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
    print("✅ Activity logs table created")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database '{DATABASE}' created successfully!")

def add_sample_data():
    """Add sample data for testing"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\n🎯 Adding sample data...\n")
    
    # Sample users
    sample_users = [
        ("John Doe", "john@gmail.com", "password123", "28", "Software developer interested in fitness"),
        ("Sarah Smith", "sarah@outlook.com", "password123", "34", "Teacher and yoga enthusiast"),
        ("Mike Johnson", "mike@yahoo.com", "password123", "42", "Business analyst")
    ]
    
    for name, email, password, age, bio in sample_users:
        try:
            hashed_pw = hash_password(password)
            cursor.execute('''
                INSERT INTO users (name, email, password, age, bio)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, hashed_pw, age, bio))
            print(f"✅ Added user: {name} ({email})")
        except sqlite3.IntegrityError:
            print(f"⚠️  User already exists: {email}")
    
    # Sample appointments
    sample_appointments = [
        ("john@gmail.com", "Dr. Meera Sharma", "2024-12-15", "10:00 AM"),
        ("sarah@outlook.com", "Dr. Arjun Patel", "2024-12-16", "02:00 PM"),
        ("john@gmail.com", "Dr. Priya Desai", "2024-12-20", "11:00 AM")
    ]
    
    for email, doctor, date, time in sample_appointments:
        cursor.execute('''
            INSERT INTO appointments (user_email, doctor, date, time)
            VALUES (?, ?, ?, ?)
        ''', (email, doctor, date, time))
    print(f"\n✅ Added {len(sample_appointments)} sample appointments")
    
    # Sample medications
    sample_medications = [
        ("john@gmail.com", "Vitamin D3", "1000 IU", "Morning", 30),
        ("john@gmail.com", "Omega-3", "1000mg", "Morning,Evening", 60),
        ("sarah@outlook.com", "Multivitamin", "1 tablet", "Morning", 90)
    ]
    
    for email, name, dosage, frequency, duration in sample_medications:
        cursor.execute('''
            INSERT INTO medications (user_email, name, dosage, frequency, duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, name, dosage, frequency, duration))
    print(f"✅ Added {len(sample_medications)} sample medications")
    
    # Sample health records
    sample_records = [
        ("john@gmail.com", "O+", 175, 70, "Jane Doe", "Wife", "+91 9876543210", "None", "Peanuts"),
        ("sarah@outlook.com", "A+", 165, 60, "Tom Smith", "Husband", "+91 9876543211", "Asthma", "None")
    ]
    
    for record in sample_records:
        cursor.execute('''
            INSERT INTO health_records 
            (user_email, blood_group, height, weight, emergency_name, emergency_relation, 
             emergency_phone, medical_conditions, allergies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', record)
    print(f"✅ Added {len(sample_records)} sample health records")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Sample data added successfully!\n")
    print("📝 Test credentials:")
    print("   Email: john@gmail.com | Password: password123")
    print("   Email: sarah@outlook.com | Password: password123")
    print("   Email: mike@yahoo.com | Password: password123\n")

def view_stats():
    """Display database statistics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\n📊 DATABASE STATISTICS")
    print("=" * 50)
    
    # Users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"👥 Total Users: {user_count}")
    
    # Appointments
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]
    print(f"📅 Total Appointments: {appointment_count}")
    
    # Medications
    cursor.execute("SELECT COUNT(*) FROM medications")
    medication_count = cursor.fetchone()[0]
    print(f"💊 Total Medications: {medication_count}")
    
    # Health Records
    cursor.execute("SELECT COUNT(*) FROM health_records")
    record_count = cursor.fetchone()[0]
    print(f"📋 Total Health Records: {record_count}")
    
    # Activity Logs
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    log_count = cursor.fetchone()[0]
    print(f"📝 Total Activity Logs: {log_count}")
    
    print("=" * 50)
    
    # Recent users
    cursor.execute('''
        SELECT name, email, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    recent_users = cursor.fetchall()
    
    if recent_users:
        print("\n👤 Recent Users:")
        for name, email, created in recent_users:
            print(f"   • {name} ({email}) - {created}")
    
    # Upcoming appointments
    cursor.execute('''
        SELECT u.name, a.doctor, a.date, a.time
        FROM appointments a
        JOIN users u ON a.user_email = u.email
        WHERE a.date >= date('now')
        ORDER BY a.date, a.time
        LIMIT 5
    ''')
    upcoming = cursor.fetchall()
    
    if upcoming:
        print("\n📅 Upcoming Appointments:")
        for name, doctor, date, time in upcoming:
            print(f"   • {name} with {doctor} on {date} at {time}")
    
    conn.close()
    print()

def reset_database():
    """Drop all tables and recreate"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\n⚠️  WARNING: This will delete all data!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("❌ Operation cancelled")
        return
    
    print("\n🗑️  Dropping all tables...")
    
    tables = ['activity_logs', 'health_records', 'medications', 'appointments', 'users']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"   ✅ Dropped {table}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database reset complete!")
    print("💡 Run option 1 to create tables again\n")

def backup_database():
    """Create a backup of the database"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}_{DATABASE}"
    
    try:
        shutil.copy2(DATABASE, backup_file)
        print(f"\n✅ Backup created: {backup_file}\n")
    except FileNotFoundError:
        print(f"\n❌ Database file '{DATABASE}' not found!\n")
    except Exception as e:
        print(f"\n❌ Backup failed: {e}\n")

def interactive_menu():
    """Interactive menu for database management"""
    while True:
        print("\n" + "=" * 60)
        print("🏥 HEALTH ASSISTANT - DATABASE MANAGER")
        print("=" * 60)
        print("\n  1. Create Database Tables")
        print("  2. Add Sample Data")
        print("  3. View Statistics")
        print("  4. Reset Database (Delete All)")
        print("  5. Backup Database")
        print("  6. Exit")
        
        choice = input("\n  Enter choice (1-6): ").strip()
        
        if choice == "1":
            create_database()
        elif choice == "2":
            add_sample_data()
        elif choice == "3":
            view_stats()
        elif choice == "4":
            reset_database()
        elif choice == "5":
            backup_database()
        elif choice == "6":
            print("\n  👋 Goodbye!\n")
            break
        else:
            print("\n  ❌ Invalid choice. Please try again.")
        
        if choice in ["1", "2", "3", "5"]:
            input("\n  Press Enter to continue...")

def main():
    """Main function"""
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n  👋 Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()