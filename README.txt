Files created:
- app.py (Flask app)
- models.py (SQLAlchemy models)
- seed_dbs.py (creates prod.db and test.db and seeds dummy data)

Run:
1) python3 /mnt/data/seed_dbs.py
2) python3 /mnt/data/app.py

Endpoints:
GET /prod -> list prod rows
GET /test -> list test rows
POST /test -> create test row (JSON body: name, region, spec, notes)
POST /replicate/test-to-prod -> push all test rows into prod
POST /pull/prod-to-test -> pull filtered rows from prod to test. JSON body: {"region": "TEST", "spec": "S1"}
