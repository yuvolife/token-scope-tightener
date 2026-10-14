"""Copy outside the business repo and replace with task-specific independent assertions.

The runner invokes this file after required checks. cwd is the modified workspace.
AB_RESPONSE_FILE names the final response; AB_RESULT_DIR names read-only evidence.
Do not import an oracle or expected answers from agent-modifiable files.
"""
import os
from pathlib import Path

response = Path(os.environ['AB_RESPONSE_FILE']).read_text()
assert response.strip(), 'missing final answer'
# Add independent behavior/boundary assertions and output-contract checks here.
# For reviews, check required known findings, locations, severity and false positives.
# For test-only tasks, test sensitivity to the known bug/mutant, not just test count.
raise SystemExit('UNCONFIGURED: replace this template with an independent correctness oracle')
