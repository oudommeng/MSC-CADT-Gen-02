import json

notebook_path = '/Users/oudommengbycha/MS_CADT_Gen-2/PY/project/project_py_v02.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        
        # 1. Uncomment seaborn
        for i, line in enumerate(source):
            if "# import seaborn as sns" in line:
                source[i] = line.replace("# import seaborn as sns", "import seaborn as sns")
        
        # 2. Normalize column names (lowercase) and handle existing capitalized names
        for i, line in enumerate(source):
            if "df.columns = df.columns.str.strip()" in line:
                source[i] = line.replace("df.columns = df.columns.str.strip()", "df.columns = df.columns.str.strip().str.lower()")
            
            # Replace common capitalized patterns with lowercase ones to prevent errors in previous cells
            # But wait, we want to BE SURE we don't break existing logic.
            # Localizing the changes to the cleaning cell:
            if "df['Order Date']" in line:
                source[i] = line.replace("df['Order Date']", "df['order date']")
            if "df['Ship Date']" in line:
                source[i] = line.replace("df['Ship Date']", "df['ship date']")
            if "df['Date Issue']" in line:
                source[i] = line.replace("df['Date Issue']", "df['date issue']")
            if "df['Sales']" in line:
                source[i] = line.replace("df['Sales']", "df['sales']")
            if "df['Profit']" in line:
                source[i] = line.replace("df['Profit']", "df['profit']")
            if "df['Discount']" in line:
                source[i] = line.replace("df['Discount']", "df['discount']")

        # 3. Create order_year after date conversion
        # We find the line where 'order date' is converted to datetime
        target_found = False
        for i, line in enumerate(source):
            if "df['order date'] = pd.to_datetime(df['order date']" in line:
                # Check if next lines already have order_year
                already_exists = False
                for j in range(i + 1, min(i + 5, len(source))):
                    if "order_year" in source[j]:
                        already_exists = True
                        break
                if not already_exists:
                    # Insert it a few lines down or right after
                    source.insert(i + 1, "df['order_year'] = df['order date'].dt.year\n")
                    target_found = True
                    break
        if target_found: continue

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent= 1)

print("Notebook updated successfully.")
