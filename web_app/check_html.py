with open(r'C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\omitted_verses_explorer.html', 'r', encoding='utf-8') as f:
    html = f.read()
print('Length of html:', len(html))
print('Contains fetch of omitted_verses_data.json?', 'omitted_verses_data.json' in html)
import re
print('Categories found in html:', set(re.findall(r'data-cat="([^"]+)"', html)))
print('Script tags or embedded data:', 'const rawData =' in html or 'const RAW_DATA =' in html or 'omitted_verses_data' in html)
