import os
for f in ['backstroke.yaml', 'breaststroke.yaml', 'butterfly.yaml']:
    path = os.path.join('config/benchmarks', f)
    with open(path, 'a', encoding='utf-8') as file:
        file.write('\n  "8-10":\n    status: INSUFFICIENT_EVIDENCE\n')
