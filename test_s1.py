import os
import glob
import re
import json

base_dir = r"c:\Users\kisho\OneDrive\Desktop\IR_Project_Consumer-Rights"
raw_dir = os.path.join(base_dir, 'data', 'raw')
processed_dir = os.path.join(base_dir, 'data', 'processed')

print(glob.glob(os.path.join(raw_dir, "*Misleading*")))
