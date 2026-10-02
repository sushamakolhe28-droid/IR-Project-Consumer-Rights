import os

base_dir = r"c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights"
raw_dir = os.path.join(base_dir, 'data', 'raw')
txt_path = os.path.join(raw_dir, 'Misleading_Ads_Guidelines_2022_OCR')

with open(txt_path, "r", encoding="latin-1") as f:
    text = f.read()

print(f"Character count: {len(text)}")
lines = text.split('\n')
for i, line in enumerate(lines[:30]):
    print(line)
