from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://Tomas:Tomas2016@127.0.0.1:3306/studyplanner"  # o tu DB actual

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def main():
    print("Conectando...")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("OK ping SELECT 1")
        tables = conn.execute(text("SHOW TABLES")).fetchall()
        print("Tablas:", [t[0] for t in tables])
        count = conn.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
        print("subjects.count =", count)

if __name__ == "__main__":
    main()
