"""
Diagnostic: traces exactly where test case generation is failing.
Runs Modules 1-7 step by step and logs counts/errors at each stage.
"""
import json
import os
import sys
import logging
from pathlib import Path
from fastapi.testclient import TestClient

# Enable detailed logging so we can see quality score rejections
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format="%(name)s %(levelname)s %(message)s")

from app.main import app

client = TestClient(app)

SCRATCH = Path(__file__).resolve().parent / "test_workspace"
os.makedirs(SCRATCH, exist_ok=True)

# --- Create a minimal React project ---
proj_dir = SCRATCH / "diag_react"
if proj_dir.exists():
    import shutil; shutil.rmtree(proj_dir)
os.makedirs(proj_dir / "src" / "components", exist_ok=True)
os.makedirs(proj_dir / "src" / "services", exist_ok=True)

(proj_dir / "package.json").write_text(json.dumps({
    "name": "diag-react-app",
    "version": "1.0.0",
    "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}
}))

(proj_dir / "src" / "components" / "LoginForm.jsx").write_text("""import React, { useState } from 'react';

export const LoginForm = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) { setError('Email required'); return; }
    onSubmit({ email, password });
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <label htmlFor="email">Email</label>
      <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      {error && <p className="error">{error}</p>}
      <label htmlFor="password">Password</label>
      <input type="password" name="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Submit</button>
    </form>
  );
};
""")

print("\\n=== Step 1: Source Ingestion (local) ===")
res = client.post("/source/local", json={"project_path": str(proj_dir.resolve())})
print(f"  Status: {res.status_code}")
if res.status_code not in (200, 201):
    print(f"  Error: {res.text}")
    sys.exit(1)
ingest = res.json()
proj_path = ingest["project_path"]
print(f"  project_path: {proj_path}")

print("\\n=== Step 2: Framework Detection ===")
res = client.post("/framework/detect", json={"project_path": proj_path})
print(f"  Status: {res.status_code}")
detect = res.json()
framework = detect.get("framework", "???")
print(f"  framework: {framework}")

print("\\n=== Step 3: Project Analysis ===")
res = client.post("/analyzer/analyze", json={"project_path": proj_path})
print(f"  Status: {res.status_code}")
if res.status_code != 200:
    print(f"  Error: {res.text}")
    sys.exit(1)
analyzer = res.json()
comps = analyzer.get("analysis", {}).get("components", [])
print(f"  Components found: {len(comps)}")
for c in comps:
    print(f"    - {c.get('name')} ({c.get('type')})")

print("\\n=== Step 4: IR Generation ===")
res = client.post("/ir/generate", json=analyzer)
print(f"  Status: {res.status_code}")
if res.status_code != 200:
    print(f"  Error: {res.text}")
    sys.exit(1)
ir = res.json()
print(f"  IR components: {len(ir.get('components', []))}")
print(f"  IR elements: {len(ir.get('elements', []))}")
print(f"  IR events: {len(ir.get('events', []))}")
print(f"  IR state: {len(ir.get('state', []))}")
print(f"  IR services: {len(ir.get('services', []))}")

print("\\n=== Step 5: Strategy Generation ===")
res = client.post("/strategy/generate", json=ir)
print(f"  Status: {res.status_code}")
if res.status_code != 200:
    print(f"  Error: {res.text}")
    sys.exit(1)
strat = res.json()
strategies = strat.get("strategies", [])
print(f"  Strategies: {len(strategies)}")
for s in strategies:
    print(f"    - [{s['id']}] cat='{s['category']}' comp='{s['target_component']}' prio={s['priority']}")

print("\\n=== Step 6: Edge Case Generation ===")
res = client.post("/edge_case/generate", json=strat)
print(f"  Status: {res.status_code}")
if res.status_code != 200:
    print(f"  Error: {res.text}")
    sys.exit(1)
ec_data = res.json()
edge_cases = ec_data.get("edge_cases", [])
print(f"  Edge cases: {len(edge_cases)}")
for ec in edge_cases:
    print(f"    - [{ec['id']}] strat={ec['strategy_id']} cat='{ec['category']}' title='{ec.get('title','')}'")

print("\\n=== Step 7: Test Case Generation ===")
res = client.post("/test_case/generate", json={
    "strategy_plan": strat,
    "edge_case_plan": ec_data
})
print(f"  Status: {res.status_code}")
if res.status_code != 200:
    print(f"  Error: {res.text}")
tc_data = res.json() if res.status_code == 200 else {}
test_cases = tc_data.get("test_cases", [])
print(f"  Test cases generated: {len(test_cases)}")
for tc in test_cases:
    print(f"    - [{tc['id']}] comp={tc.get('component')} cat={tc.get('category')} score={tc.get('test_quality_score')}")

# Now manually check generator.supports() matching
print("\\n=== DIAGNOSTIC: Matching edge cases to generators ===")
from app.services.test_case_generator.test_case_generator import _build_default_test_case_registry
from app.models.strategy_models import TestStrategy
from app.models.edge_case_models import EdgeCaseScenario

registry = _build_default_test_case_registry()
generators = registry.get_generators()
strategy_map = {s["id"]: TestStrategy.model_validate(s) for s in strategies}

for ec_dict in edge_cases:
    ec = EdgeCaseScenario.model_validate(ec_dict)
    strat_obj = strategy_map.get(ec.strategy_id)
    if not strat_obj:
        print(f"  EC [{ec.id}]: NO STRATEGY FOUND for strategy_id='{ec.strategy_id}'")
        continue
    matched = False
    for gen in generators:
        if gen.supports(strat_obj, ec):
            matched = True
            print(f"  EC [{ec.id}]: MATCHED by {gen.__class__.__name__} (ec.cat='{ec.category}', strat.cat='{strat_obj.category}')")
            break
    if not matched:
        print(f"  EC [{ec.id}]: NO GENERATOR MATCH (ec.cat='{ec.category}', strat.cat='{strat_obj.category}')")

print("\\n=== DONE ===")
