from flask import Flask, jsonify, request
from models import get_engine, get_session, ProdTable, TestTable, Base
from sqlalchemy import select, insert, update, text, func
from sqlalchemy.orm import Session
import uuid
from pathlib import Path

app = Flask(__name__)

PROD_DB = "/mnt/data/prod.db"
TEST_DB = "/mnt/data/test.db"

prod_engine = get_engine(PROD_DB)
test_engine = get_engine(TEST_DB)

ProdSession = get_session(prod_engine)
TestSession = get_session(test_engine)

# Simple helper to serialize rows
def serialize_prod(row):
    return {
        "id": row.id,
        "name": row.name,
        "region": row.region,
        "spec": row.spec,
        "notes": row.notes,
        "last_modified": getattr(row, "last_modified", None)
    }

def serialize_test(row):
    return {
        "id": row.id,
        "name": row.name,
        "region": row.region,
        "spec": row.spec,
        "notes": row.notes,
        "origin_system": row.origin_system,
        "change_id": row.change_id,
        "last_modified": getattr(row, "last_modified", None)
    }

@app.route('/prod', methods=['GET'])
def list_prod():
    \"\"\"List all rows in prod DB\"\"\"
    with ProdSession() as s:
        rows = s.query(ProdTable).all()
        return jsonify([serialize_prod(r) for r in rows])

@app.route('/test', methods=['GET'])
def list_test():
    \"\"\"List all rows in test DB\"\"\"
    with TestSession() as s:
        rows = s.query(TestTable).all()
        return jsonify([serialize_test(r) for r in rows])

@app.route('/test', methods=['POST'])
def create_test_row():
    \"\"\"Create a row in test DB\"\"\"
    payload = request.json or {}
    name = payload.get('name') or 'Untitled'
    region = payload.get('region') or 'TEST'
    spec = payload.get('spec') or 'S1'
    notes = payload.get('notes') or None
    origin = payload.get('origin_system') or 'TEST'
    change_id = payload.get('change_id') or str(uuid.uuid4())

    with TestSession() as s:
        new = TestTable(name=name, region=region, spec=spec, notes=notes, origin_system=origin, change_id=change_id)
        s.add(new)
        s.commit()
        return jsonify({"ok": True, "id": new.id}), 201

@app.route('/replicate/test-to-prod', methods=['POST'])
def replicate_test_to_prod():
    \"\"\"Push all rows from TEST -> PROD (unfiltered). This acts as the Test->Prod full sync.\"\"\"
    # Business logic: skip rows that originated from PROD (origin_system == 'PROD')
    pushed = 0
    errors = []
    from sqlalchemy.exc import SQLAlchemyError
    with TestSession() as ts, ProdSession() as ps:
        rows = ts.query(TestTable).all()
        for r in rows:
            try:
                # check if row already exists in prod by unique business key (here: name + spec) or id
                existing = ps.query(ProdTable).filter(ProdTable.id == r.id).one_or_none()
                if existing:
                    # update existing prod row
                    existing.name = r.name
                    existing.region = r.region
                    existing.spec = r.spec
                    existing.notes = r.notes
                else:
                    # insert — preserve id if you want, otherwise let prod autoincrement
                    newp = ProdTable(name=r.name, region=r.region, spec=r.spec, notes=r.notes)
                    ps.add(newp)
                ps.commit()
                pushed += 1
            except SQLAlchemyError as e:
                ps.rollback()
                errors.append({"id": r.id, "error": str(e)})
    return jsonify({"pushed": pushed, "errors": errors})

@app.route('/pull/prod-to-test', methods=['POST'])
def pull_filtered_prod_to_test():
    \"\"\"Pull filtered rows from PROD -> TEST. Use filter parameters passed in JSON body.\n       Example body: {\"region\": \"TEST\", \"spec\": \"S1\"}\n    \"\"\"
    payload = request.json or {}
    region = payload.get('region')
    spec = payload.get('spec')

    # Build a simple filter — only rows matching ALL provided non-null filters are pulled
    with ProdSession() as ps, TestSession() as ts:
        q = ps.query(ProdTable)
        if region:
            q = q.filter(ProdTable.region == region)
        if spec:
            q = q.filter(ProdTable.spec == spec)
        rows = q.all()
        inserted = 0
        for r in rows:
            # check if exists in test by a business key (name + spec) to avoid duplicates
            exists = ts.query(TestTable).filter(TestTable.name == r.name, TestTable.spec == r.spec).one_or_none()
            if exists:
                # update existing test row
                exists.region = r.region
                exists.notes = r.notes
            else:
                t = TestTable(name=r.name, region=r.region, spec=r.spec, notes=r.notes, origin_system='PROD', change_id=str(uuid.uuid4()))
                ts.add(t)
                inserted += 1
        ts.commit()
    return jsonify({"pulled": len(rows), "inserted": inserted})

if __name__ == '__main__':
    # Run Flask app for quick testing
    app.run(host='0.0.0.0', port=5000, debug=True)
