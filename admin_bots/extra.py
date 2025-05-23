from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from db import engine


def create_table_if_not_exists(table_name: str, create_sql: str):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        print(f"Creating '{table_name}' table...")
        try:
            with engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
                print(f"'{table_name}' table created successfully.")
        except (ProgrammingError, OperationalError) as e:
            print(f"Failed to create table '{table_name}': {e}")
    else:
        print(f"'{table_name}' table already exists.")


def add_column_if_not_exists(table: str, column: str, alter_sql: str):
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table)]

        if column not in columns:
            print(f"Adding '{column}' column to '{table}' table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"'{column}' column added to '{table}' successfully.")
            except (ProgrammingError, OperationalError) as e:
                print(f"Failed to add column '{column}' to '{table}': {e}")
        else:
            print(f"'{column}' column already exists in '{table}'.")
    except Exception as e:
        print(f"Error checking table '{table}': {e}")


def setup_hakobot_schema():
    inspector = inspect(engine)

    # ایجاد جدول payments با admin_id
    create_table_if_not_exists(
        "payments",
        """
        CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT NOT NULL,
            amount BIGINT NOT NULL,
            payment_type ENUM('deposit', 'withdraw') NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
        """
    )

    # افزودن ستون hakobot_balance به جدول admins
    add_column_if_not_exists(
        "admins",
        "hakobot_balance",
        "ALTER TABLE admins ADD COLUMN hakobot_balance BIGINT NOT NULL DEFAULT 0"
    )

    add_column_if_not_exists(
        "admins",
        "hakobot_gb_fee",
        "ALTER TABLE admins ADD COLUMN hakobot_gb_fee BIGINT NOT NULL DEFAULT 2000"
    )

if __name__ == "__main__":
    setup_hakobot_schema()