import os
import shutil
from PIL import Image, ImageChops

def trim_borders(img):
    # 1. Try standard getbbox (works for transparency)
    bbox = img.getbbox()
    
    # If bbox is None (fully transparent) or full size, check for solid color background
    if not bbox:
        return img, None
        
    width, height = img.size
    if bbox == (0, 0, width, height):
        # Check if it's a solid background (e.g. white/colored splash)
        # Get top-left pixel color
        bg_color = img.getpixel((0, 0))
        
        # Create a background image of the same color
        bg = Image.new(img.mode, img.size, bg_color)
        
        # Find difference
        diff = ImageChops.difference(img, bg)
        # Enhance difference to catch subtle variations
        diff = ImageChops.add(diff, diff, 2.0, -100)
        
        bbox_diff = diff.getbbox()
        if bbox_diff:
            # Found content inside solid background
            print(f"  Detected solid background {bg_color}, cropping to content.")
            return img.crop(bbox_diff), bbox_diff
        else:
            # Truly empty or solid image
            return img, bbox
            
    # Standard transparency crop
    return img.crop(bbox), bbox

def process_image(file_path):
    if not os.path.exists(file_path):
        print(f"Skipping missing file: {file_path}")
        return

    print(f"Processing {file_path}...")
    
    try:
        # Backup
        backup_path = file_path + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy(file_path, backup_path)
            print(f"  Backed up to {os.path.basename(backup_path)}")
        
        img = Image.open(file_path).convert("RGBA")
        original_size = img.size
        
        # Trim
        img_cropped, bbox = trim_borders(img)
        
        if img_cropped == img or (bbox and (bbox[2]-bbox[0] >= original_size[0] and bbox[3]-bbox[1] >= original_size[1])):
            print("  Image already maximized or empty.")
            # Even if it's "full", the user might want to ensure it's centered/fit if it wasn't?
            # But if it's already full, we can't "expand" it further.
            # However, `trim_borders` might return the original image if it failed to find a bbox.
            pass
        else:
            print(f"  Cropped from {original_size} to {img_cropped.size} (bbox: {bbox})")

        # Resize to fit original dimensions (Maximize)
        # We want to fit the cropped content into the original_size
        target_size = original_size
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        width_ratio = target_size[0] / img_cropped.width
        height_ratio = target_size[1] / img_cropped.height
        
        scale_factor = min(width_ratio, height_ratio)
        
        new_width = int(img_cropped.width * scale_factor)
        new_height = int(img_cropped.height * scale_factor)
        
        # Only resize if dimensions changed
        if new_width != img_cropped.width or new_height != img_cropped.height:
            print(f"  Resizing to {new_width}x{new_height} to fit {target_size}")
            img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            img_resized = img_cropped
            
        # Center
        x = (target_size[0] - new_width) // 2
        y = (target_size[1] - new_height) // 2
        
        new_img.paste(img_resized, (x, y))
        
        # Save
        new_img.save(file_path)
        print("  Done.")
        
    except Exception as e:
        print(f"  Error: {e}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    files = [
        os.path.join(base_dir, 'assets', 'icon.png'),
        os.path.join(base_dir, 'assets', 'splash.png'),
        os.path.join(base_dir, 'assets', 'splash-dark.png'),
        os.path.join(base_dir, 'dist', 'static', 'img', 'icon-192.png'),
        os.path.join(base_dir, 'dist', 'static', 'img', 'icon-512.png')
    ]
    
    for f in files:
        process_image(f)

if __name__ == "__main__":
    main()
