import os
import hashlib
import json

# Define paths
DEV_ROOT = os.path.join("scripts", "explain_verbs")
DEV_STATIC = os.path.join(DEV_ROOT, "static")
DEV_INDEX = os.path.join(DEV_ROOT, "templates", "index.html")

DIST_ROOT = "dist"
DIST_STATIC = os.path.join(DIST_ROOT, "static")
DIST_INDEX = os.path.join(DIST_ROOT, "index.html")

def calculate_hash(file_path):
    """Calculate SHA256 hash of a file."""
    if not os.path.exists(file_path):
        return None
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compare_file(dev_path, dist_path, label):
    """Compare two files and print result."""
    dev_hash = calculate_hash(dev_path)
    dist_hash = calculate_hash(dist_path)
    
    if not dev_hash:
        print(f"❌ [MISSING IN DEV] {label}")
        return False
    if not dist_hash:
        print(f"❌ [MISSING IN DIST] {label}")
        return False
        
    if dev_hash == dist_hash:
        print(f"✅ [MATCH] {label}")
        return True
    else:
        # Special case for index.html which is expected to differ slightly (injection removed)
        if "index.html" in label:
             print(f"⚠️ [DIFF]  {label} (Expected due to script injection removal)")
        else:
             print(f"❌ [DIFF]  {label}")
        return False

def compare_dir(dev_dir, dist_dir, rel_path=""):
    """Recursively compare directories."""
    # List all files in dev
    try:
        dev_files = os.listdir(dev_dir)
    except FileNotFoundError:
        print(f"❌ [MISSING DIR] {dev_dir}")
        return

    for f in dev_files:
        dev_f = os.path.join(dev_dir, f)
        dist_f = os.path.join(dist_dir, f)
        rel_f = os.path.join(rel_path, f)
        
        if os.path.isdir(dev_f):
            # Recurse
            compare_dir(dev_f, dist_f, rel_f)
        else:
            # Compare file
            compare_file(dev_f, dist_f, rel_f)

def main():
    print("=== Comparing Dev vs Static Files ===")
    
    # 1. Compare index.html
    compare_file(DEV_INDEX, DIST_INDEX, "index.html")
    
    # 2. Compare Static Assets
    print("\n--- Static Assets ---")
    subfolders = ["js", "css", "img", "lib"]
    for folder in subfolders:
        compare_dir(os.path.join(DEV_STATIC, folder), os.path.join(DIST_STATIC, folder), folder)
        
    # 3. Compare Data Files
    print("\n--- Data Files ---")
    data_files = ["legacy_data.json", "netem_full_list.json", "manifest.json", "sw.js"]
    for file in data_files:
        compare_file(os.path.join(DEV_STATIC, file), os.path.join(DIST_STATIC, file), file)

if __name__ == "__main__":
    main()
