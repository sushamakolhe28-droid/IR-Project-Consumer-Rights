import os
import re
import json

base_dir = os.path.dirname(os.path.dirname(__file__))
raw_dir = os.path.join(base_dir, 'data', 'raw')

txt_path = os.path.join(raw_dir, 'Misleading_Ads_Guidelines_2022_OCR.txt')
if not os.path.exists(txt_path):
    print(f"Error: {txt_path} not found.")
else:
    print(f"Found {txt_path}")
