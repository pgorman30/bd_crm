from db.database import ENGINE
from db.models import Base

def main():
    Base.metadata.create_all(bind=ENGINE)
    print("✅ Database initialized / migrated.")

if __name__ == "__main__":
    main()