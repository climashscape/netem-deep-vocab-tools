import os
import shutil
from PIL import Image

def maximize_icon(icon_path):
    try:
        print(f"Processing {icon_path}...")
        img = Image.open(icon_path).convert("RGBA")
        
        # 1. Trim transparent borders
        bbox = img.getbbox()
        if not bbox:
            print("Warning: Image seems empty/transparent")
            return
            
        print(f"Original content bounds: {bbox}")
        
        # Crop to content only
        img_cropped = img.crop(bbox)
        
        # 2. Resize to 1024x1024 (Stretch/Fit)
        # Since we want to "expand" it to remove empty borders, we resize the cropped content
        # directly to the target size. 
        # However, to avoid distortion, we should fit it into 1024x1024 maintaining aspect ratio,
        # and fill the rest with the background color if it's not perfectly square.
        
        target_size = (1024, 1024)
        new_img = Image.new("RGBA", target_size, (0, 0, 0, 0)) # Transparent background first
        
        # Calculate resize keeping aspect ratio
        width_ratio = target_size[0] / img_cropped.width
        height_ratio = target_size[1] / img_cropped.height
        
        # To fill the space as much as possible without cutting off, we use min ratio
        # To fill the space completely (maybe cutting off), we use max ratio
        # User said "enlarge to remove empty borders".
        # Assuming the content is the icon itself.
        
        scale_factor = min(width_ratio, height_ratio)
        
        new_width = int(img_cropped.width * scale_factor)
        new_height = int(img_cropped.height * scale_factor)
        
        print(f"Resizing content to {new_width}x{new_height}")
        
        img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Paste centered
        x = (target_size[0] - new_width) // 2
        y = (target_size[1] - new_height) // 2
        
        # If the user wants a solid background, we should probably pick one?
        # But if the original icon had transparency, we might want to keep it?
        # The user said "remove empty borders".
        # Let's check the corner pixel of the original image to see if it has a background color.
        
        # Strategy: 
        # If the cropped image is almost square, just resize it to 1024x1024.
        # If it's not, we center it.
        
        new_img.paste(img_resized, (x, y))
        
        # Save
        new_img.save(icon_path)
        print(f"Saved maximized icon to {icon_path}")
        
    except Exception as e:
        print(f"Error optimizing {icon_path}: {e}")
        import traceback
        traceback.print_exc()

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_icon = os.path.join(base_dir, 'assets', 'icon.png')
    
    if os.path.exists(assets_icon):
        # We don't backup again if we want to overwrite the previous attempt
        # But if the user wants to start from scratch...
        # Let's check if there is an original backup
        backup_path = os.path.join(base_dir, 'assets', 'icon_original.png')
        
        source_path = assets_icon
        if os.path.exists(backup_path):
             print(f"Found original backup at {backup_path}, using it as source.")
             source_path = backup_path
        
        # Create a temp copy to work on
        temp_work_path = os.path.join(base_dir, 'assets', 'icon_temp_work.png')
        shutil.copy(source_path, temp_work_path)
        
        maximize_icon(temp_work_path)
        
        # If successful, overwrite the main icon
        if os.path.exists(temp_work_path):
            shutil.move(temp_work_path, assets_icon)
            
            # Also update dist icons
            img = Image.open(assets_icon)
            img.resize((192, 192), Image.Resampling.LANCZOS).save(os.path.join(base_dir, 'dist', 'static', 'img', 'icon-192.png'))
            img.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(base_dir, 'dist', 'static', 'img', 'icon-512.png'))
            print("Updated web icons.")

if __name__ == "__main__":
    main()
