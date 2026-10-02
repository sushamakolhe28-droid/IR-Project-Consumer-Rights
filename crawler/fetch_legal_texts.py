import os
import requests
import time

def download_file(url, output_path):
    print(f"Downloading {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully saved to {output_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    sources = [
        {
            "name": "Consumer Protection Act 2019",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/15256/1/a2019-35.pdf",
            "filename": "CPA_2019.pdf"
        },
        {
            "name": "Consumer Protection (E-Commerce) Rules 2020",
            # Example placeholder URL, real URL to be verified
            "url": "https://consumeraffairs.nic.in/sites/default/files/E%20commerce%20rules.pdf", 
            "filename": "Ecommerce_Rules_2020.pdf"
        },
        {
            "name": "Guidelines for Prevention and Regulation of Dark Patterns 2023",
            "url": "https://pib.gov.in/PressReleasePage.aspx?PRID=1981324", # Webpage version
            "filename": "Dark_Patterns_Guidelines.html"
        }
    ]
    
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    
    for source in sources:
        output_path = os.path.join(base_dir, source["filename"])
        if not os.path.exists(output_path):
            download_file(source["url"], output_path)
            time.sleep(2) # Be polite
        else:
            print(f"File {output_path} already exists, skipping.")

if __name__ == "__main__":
    main()
