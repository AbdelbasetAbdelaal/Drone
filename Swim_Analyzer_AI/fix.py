import os

app_dir = 'D:/AI_Projects/Swim_Analyzer_AI/app'
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            if 'use_container_width=True' in content:
                content = content.replace('use_container_width=True', 'width="stretch"')
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f'Replaced in {path}')
