import os
import hashlib
from PIL import Image
from collections import defaultdict


def hash_image(image_path):
    """Generate a hash for an image file."""
    hasher = hashlib.md5()
    try:
        with open(image_path, 'rb') as img_file:
            buf = img_file.read()
            hasher.update(buf)
    except Exception as e:
        print(f"Error hashing image {image_path}: {e}")
        return None
    return hasher.hexdigest()


def find_duplicates(root_folder):
    """Find duplicate images by name and content."""
    image_files = []
    for root, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff')):
                image_files.append(os.path.join(root, file))

    print(f"Found {len(image_files)} images in total.")

    name_dict = defaultdict(list)
    hash_dict = defaultdict(list)

    for idx, image_path in enumerate(image_files):
        image_name = os.path.basename(image_path)
        name_dict[image_name].append(image_path)

        image_hash = hash_image(image_path)
        if image_hash:
            hash_dict[image_hash].append(image_path)

        if (idx + 1) % 100 == 0 or idx == len(image_files) - 1:
            print(f"Processed {idx + 1}/{len(image_files)} images.")

    duplicate_names = {name: paths for name, paths in name_dict.items() if len(paths) > 1}
    duplicate_hashes = {image_hash: paths for image_hash, paths in hash_dict.items() if len(paths) > 1}

    return duplicate_names, duplicate_hashes


def main():
    root_folder = 'dataset gatherer'  # Change this to your folder path
    duplicate_names, duplicate_hashes = find_duplicates(root_folder)

    print("\nDuplicate image names:")
    for name, paths in duplicate_names.items():
        print(f"{name}: {paths}")

    print("\nDuplicate image content:")
    for image_hash, paths in duplicate_hashes.items():
        print(f"{image_hash}: {paths}")


if __name__ == "__main__":
    main()
