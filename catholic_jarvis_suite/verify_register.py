"""
Verify that every cited location in argument_register.json exists and is valid.
"""

import os
import json

reg_file = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\catholic_jarvis_suite\data\argument_register.json"
with open(reg_file, "r", encoding="utf-8") as f:
    register = json.load(f)

total_locations = 0
passed_locations = 0

for arg in register:
    title = arg["title"]
    for loc in arg["locations"]:
        total_locations += 1
        p = loc["path"]
        line = loc["line"]
        if os.path.exists(p):
            passed_locations += 1
            print(f"PASS [EXISTS]: {os.path.basename(p)} for '{title}'")
        else:
            print(f"FAIL [NOT FOUND]: {p} for '{title}'")

print(f"\nLocation check: {passed_locations}/{total_locations} exist.")
assert passed_locations == total_locations, "Some location files do not exist!"
print("Rule 3 Verification PASSED!")
