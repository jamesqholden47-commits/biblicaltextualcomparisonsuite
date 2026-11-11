with open(r'C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\omitted_verses_explorer.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
matches = re.findall(r'const\s+([A-Za-z0-9_]+)\s*=', html)
print('JS Constants:', matches)
matches_var = re.findall(r'let\s+([A-Za-z0-9_]+)\s*=', html)
print('JS Lets:', matches_var)
matches_var2 = re.findall(r'var\s+([A-Za-z0-9_]+)\s*=', html)
print('JS Vars:', matches_var2)
