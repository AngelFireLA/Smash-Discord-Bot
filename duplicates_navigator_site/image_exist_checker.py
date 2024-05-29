import os
from duplicates_dict import duplicates  # Import the generated duplicates dictionary

def check_image_paths(duplicates):
    missing_images = []
    found_images = []

    for hash_value, paths in duplicates.items():
        for path in paths:
            full_path = os.path.join('static', path.replace("\\", "/"))
            if os.path.exists(full_path):
                found_images.append(full_path)
            else:
                missing_images.append(full_path)

    return found_images, missing_images

if __name__ == "__main__":
    found_images, missing_images = check_image_paths(duplicates)

    if missing_images:
        print("Missing images:")
        for path in missing_images:
            print(path)
    else:
        print("All images found successfully.")

    if found_images:
        print("\nFound images:")
        for path in found_images:
            print(path)
