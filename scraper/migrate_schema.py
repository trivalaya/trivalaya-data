import mysql.connector
import os
from dotenv import load_dotenv

# Load your new .env file
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("TRIVALAYA_DB_HOST", "127.0.0.1"),
    "user": os.getenv("TRIVALAYA_DB_USER", "root"),
    "password": os.getenv("TRIVALAYA_DB_PASSWORD"),
    "database": os.getenv("TRIVALAYA_DB_NAME", "auction_data")
}

def migrate():
    print("🔌 Connecting to Database...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # List of columns to add (Name, Type)
    new_columns = [
        ("auction_house", "VARCHAR(50)"),
        ("sale_id", "VARCHAR(50)"),
        ("currency", "VARCHAR(10) DEFAULT 'USD'"),
        ("normalized_image_path", "TEXT"),
        ("layer2_culture", "VARCHAR(50)"),
        ("layer3_period", "VARCHAR(50)"),
        ("embedding_vector", "LONGBLOB"), # Binary storage for vectors
        ("human_verified", "BOOLEAN DEFAULT FALSE"),
        ("verified_label", "VARCHAR(50)")
    ]

    print("🛠  Migrating Schema...")
    
    for col_name, col_type in new_columns:
        try:
            # Attempt to add the column
            cursor.execute(f"ALTER TABLE auction_data ADD COLUMN {col_name} {col_type}")
            print(f"   ✅ Added column: {col_name}")
        except mysql.connector.errors.ProgrammingError as e:
            # Error 1060 means "Duplicate column name" - it already exists
            if e.errno == 1060:
                print(f"   ℹ️  Column exists: {col_name} (Skipping)")
            else:
                print(f"   ❌ Error adding {col_name}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✨ Migration Complete.")

if __name__ == "__main__":
    migrate()