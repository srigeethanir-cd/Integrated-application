import tempfile, shutil
from pathlib import Path
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.ir_generator.ir_generator_service import IRGeneratorService
from app.services.test_strategy.strategy_engine_service import StrategyEngine
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService

td = tempfile.mkdtemp()
p = Path(td)
(p / "package.json").write_text('{"name": "test-app", "dependencies": {"react": "^18.2.0"}}')
src = p / "src"
src.mkdir()
(src / "UserProfile.jsx").write_text("""
import React, { useState } from 'react';
export default function UserProfile({ userId, onUpdate }) {
    const [name, setName] = useState('');
    const handleSave = async (e) => { e.preventDefault(); };
    return (
        <form onSubmit={handleSave}>
            <input value={name} onChange={(e) => setName(e.target.value)} />
            <button type='submit'>Save</button>
        </form>
    );
}
""")
an = ProjectAnalyzerService().analyze(str(p))
ir = IRGeneratorService().generate_ir(an)
st = StrategyEngine().generate_strategies(ir)
tc = TestCaseGeneratorService().generate_test_cases(st)
print('COUNT:', tc.total_test_cases)
for i, c in enumerate(tc.test_cases):
    print(f"{i+1}. [{c.component}] [{c.target_function}] {c.id} | {c.title}")
shutil.rmtree(td, ignore_errors=True)
