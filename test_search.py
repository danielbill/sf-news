import sys
sys.path.insert(0, 'D:/workspace/cybcortex/1技能库/py_code')

from gather.search.semantic_search import semantic_search

result = semantic_search(
    query='埃隆·马斯克 创始人 简介',
    instruction='生成人物档案',
    max_results=5
)

if result.get('summary'):
    print("Success!")
    print(result.get('summary')[:500])
else:
    print("Error:", result.get('error', 'Unknown'))
