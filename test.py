def show_folder_structure():
    import os

    # You can replace this with any directory path you want to explore
    folder_path = r"D:\Dev\Python\Smash-Discord-Bot\dataset gatherer"

    def is_image_file(file):
        image_extensions = ['.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        return any(file.lower().endswith(ext) for ext in image_extensions)

    def explore_folder(path, indent=0):
        try:
            items = os.listdir(path)
        except PermissionError:
            print(" " * indent + "[Permission Denied]")
            return

        files = []
        images_count = 0
        folders = []

        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif os.path.isfile(item_path):
                if is_image_file(item):
                    images_count += 1
                else:
                    files.append(item)

        # Print current directory
        print(" " * indent + os.path.basename(path) + '/')

        # Print subdirectories
        for folder in folders:
            explore_folder(os.path.join(path, folder), indent + 4)
            print()

        # Print the number of images if any
        if images_count > 0:
            print(" " * (indent+3) + f"{images_count} image(s)")

        # Print files
        for file in files:
            print(" " * indent + file)

    explore_folder(folder_path)


# Call the function to display the folder structure
show_folder_structure()
