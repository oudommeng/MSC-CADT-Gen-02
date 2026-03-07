import json

notebook_path = '/Users/oudommengbycha/MS_CADT_Gen-2/PY/project/project_py_v02.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The target line to find: "df['Month'] = df['Order Date'].dt.to_period('M')\n"
# We want to insert "df['order_year'] = df['Order Date'].dt.year\n" after it.

inserted = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if "df['Month'] = df['Order Date'].dt.to_period('M')" in line:
                # Check if it's already there to avoid duplicates
                if i + 1 < len(source) and "df['order_year']" in source[i+1]:
                    continue
                
                # Insert the new line. Keep the newline character if present.
                new_line = "df['order_year'] = df['Order Date'].dt.year\n"
                source.insert(i + 1, new_line)
                inserted = True
                break
    if inserted:
        break

if inserted:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Successfully updated the notebook.")
else:
    print("Target line not found in the notebook.")
