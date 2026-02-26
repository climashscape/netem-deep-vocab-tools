import os
import shutil
import sys

# Define paths
# SOURCE: The Dev environment (scripts/explain_verbs)
DEV_ROOT = os.path.join("scripts", "explain_verbs")
DEV_TEMPLATES = os.path.join(DEV_ROOT, "templates")
DEV_STATIC = os.path.join(DEV_ROOT, "static")

# DESTINATION: The Static build (dist)
DIST_ROOT = "dist"
DIST_STATIC = os.path.join(DIST_ROOT, "static")

def sync_file(src, dst):
    """Copy a single file if it exists."""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Synced: {src} -> {dst}")
    else:
        print(f"Warning: Source file not found: {src}")

def sync_dir(src_dir, dst_dir):
    """Copy an entire directory tree."""
    if os.path.exists(src_dir):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        print(f"Synced Dir: {src_dir} -> {dst_dir}")
    else:
        print(f"Warning: Source dir not found: {src_dir}")

def main():
    print("=== Starting Full Sync from Dev to Static ===")
    
    # 1. Sync index.html
    # Dev uses templates/index.html, Static uses dist/index.html
    sync_file(os.path.join(DEV_TEMPLATES, "index.html"), os.path.join(DIST_ROOT, "index.html"))
    
    # 2. Sync Static Assets (JS, CSS, Libs)
    # Dev uses scripts/explain_verbs/static/*, Static uses dist/static/*
    # We exclude the 'static' nested folder if it exists in source to avoid recursion issues
    # But based on LS, the structure seems flat in source.
    
    # Sync specific subfolders to be safe and precise
    subfolders = ["js", "css", "img", "lib"]
    for folder in subfolders:
        src = os.path.join(DEV_STATIC, folder)
        dst = os.path.join(DIST_STATIC, folder)
        if os.path.exists(src):
            sync_dir(src, dst)

    # 3. Sync Data Files (JSONs)
    # legacy_data.json and netem_full_list.json
    data_files = ["legacy_data.json", "netem_full_list.json", "manifest.json", "sw.js"]
    for file in data_files:
        src = os.path.join(DEV_STATIC, file)
        # sw.js usually sits in root for scope reasons, but let's check source
        if file == "sw.js":
             # If sw.js is in static in dev, it might need to go to root in dist
             # But let's follow the standard pattern first
             pass

        # Try to sync to dist/static/
        sync_file(src, os.path.join(DIST_STATIC, file))
        
        # Also copy sw.js to root if it exists
        if file == "sw.js" and os.path.exists(src):
             sync_file(src, os.path.join(DIST_ROOT, "sw.js"))

    print("=== Sync Complete ===")
    print("NOTE: You may need to manually remove the Dev-mode specific script injection")
    print("from dist/index.html if it interferes with production (though it should be harmless).")

if __name__ == "__main__":
    main()
