import mysql.connector

class DatabaseHandler:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.ssl_disabled = True
        self.setup_database()

    def setup_database(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                ssl_disabled=self.ssl_disabled
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            conn.commit()
            cursor.close()
            conn.close()

            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                ssl_disabled=self.ssl_disabled
            )
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auction_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    lot_number INT NOT NULL,
                    title TEXT,
                    description TEXT,
                    current_bid VARCHAR(255),
                    image_url TEXT,
                    image_path TEXT,
                    closing_date VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Database error: {e}")

    def insert_data(self, data):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                ssl_disabled=self.ssl_disabled
            )
            cursor = conn.cursor()
            query = '''
                INSERT INTO auction_data (lot_number, title, description, current_bid, image_url,image_path, closing_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                data.get("lot_number"),
                data.get("title", "No Title"),
                data.get("description", "No Description"),
                data.get("current_bid", "0"),
                data.get("image_url", ""),
                data.get("image_path", ""),
                data.get("closing_date", "N/A")
            )
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Insert error: {e}")
