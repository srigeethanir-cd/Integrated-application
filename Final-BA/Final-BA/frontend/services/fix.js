const fs = require('fs');
const path = 'd:/Design/Final-BA/Final-BA/frontend/services/mockWorkflowState.ts';
let content = fs.readFileSync(path, 'utf8');
content = content.replace(/status: 'approved'/g, "status: 'needs_review'");
fs.writeFileSync(path, content);
console.log('done');
