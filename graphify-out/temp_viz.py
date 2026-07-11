import json
from graphify.html import generate_html
from pathlib import Path

analysis = json.loads(Path('graphify-out/.graphify_analysis.json').read_text(encoding='utf-8'))
labels = {k: 'Community ' + str(k) for k in analysis['communities'].keys()}

generate_html(Path('graphify-out/graph.json'), labels, Path('graphify-out/index.html'))
print('Generated graphify-out/index.html')
