#!/usr/bin/env python3
import os
import base64
import json

OUTPUT_DIR = "assets/processed"

def png_to_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def main():
    config_path = os.path.join(OUTPUT_DIR, "watermark-config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    base64_data = {}
    for key, cfg in config.items():
        filepath = os.path.join(OUTPUT_DIR, cfg['file'])
        if os.path.exists(filepath):
            b64 = png_to_base64(filepath)
            base64_data[key] = f"data:image/png;base64,{b64}"
            print(f"{key}: {len(b64)} chars")
    
    output_path = os.path.join(OUTPUT_DIR, "watermark-base64.json")
    with open(output_path, 'w') as f:
        json.dump(base64_data, f)
    print(f"\nSaved: {output_path}")
    
    total = sum(len(v) for v in base64_data.values())
    print(f"Total Base64 size: {total / 1024:.1f} KB")

if __name__ == "__main__":
    main()
