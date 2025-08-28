import re

file_path = "app.py"

with open(file_path, "r", encoding="utf-8") as file:
    content = file.read()

# Автоматическая замена одинарных `\` на `\\` только внутри f-строк
fixed_content = re.sub(r'f"([^"]*?)\\([^"]*?)"', r'f"\1\\\\\2"', content)

with open(file_path, "w", encoding="utf-8") as file:
    file.write(fixed_content)

