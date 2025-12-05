# Run this to create two sqlite DB files (prod.db, test.db)
from models import Base, ProdTable, TestTable, get_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import uuid

def seed():
    prod_path = Path("/mnt/data/prod.db")
    test_path = Path("/mnt/data/test.db")

    # Remove existing DBs for a fresh start (comment out if you want persistence)
    if prod_path.exists():
        prod_path.unlink()
    if test_path.exists():
        test_path.unlink()

    prod_engine = get_engine(str(prod_path))
    test_engine = get_engine(str(test_path))

    Base.metadata.create_all(prod_engine)
    Base.metadata.create_all(test_engine)

    ProdSession = sessionmaker(bind=prod_engine)
    TestSession = sessionmaker(bind=test_engine)

    # Seed PROD with some rows (only a subset will be pulled to TEST by filter)
    with ProdSession() as s:
        s.add_all([
            ProdTable(name="Widget A", region="PROD-APAC", spec="S1", notes="Important prod row"),
            ProdTable(name="Widget B", region="TEST", spec="S2", notes="Should be filtered to test"),
            ProdTable(name="Gadget C", region="TEST", spec="S1", notes="Should be filtered to test"),
            ProdTable(name="Gizmo D", region="PROD-EU", spec="S3", notes="Prod only"),
        ])
        s.commit()

    # Seed TEST with some rows (these will be able to be pushed to PROD)
    with TestSession() as s:
        s.add_all([
            TestTable(name="Test Item 1", region="TEST", spec="S1", notes="Created in test", origin_system="TEST", change_id=str(uuid.uuid4())),
            TestTable(name="Test Item 2", region="TEST", spec="S2", notes="Another test row", origin_system="TEST", change_id=str(uuid.uuid4())),
            TestTable(name="Hidden Item", region="QA", spec="S9", notes="This row may not be targeted by filters", origin_system="TEST", change_id=str(uuid.uuid4())),
        ])
        s.commit()

    print("Created prod.db and test.db with sample rows.\\nprod.db and test.db are in /mnt/data/")

if __name__ == '__main__':
    seed()
