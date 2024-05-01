import os
import re
import argparse
import subprocess

def find_libraries(library_stems, search_paths, extension):
    library_paths = []
    for library_stem in library_stems:
        library = []
        for search_path in search_paths:
            try:
                files = os.listdir(search_path)
                pattern = r"^(?:lib)?{}(?:-(?:\d+\.)*|\d+\.|\.){}$".format(library_stem, extension)
                library.extend([
                    {"filename": filename, "base_path": search_path} for filename in files
                    if re.search(pattern, filename)
                ])
            except FileNotFoundError:
                print(f"Warning: The path {search_path} does not exist.")
                continue

        if not library:
            raise AssertionError(f"No libraries found in {search_paths} which match \"{library_stem}\" stem")
        if len(library) != 1:
            raise AssertionError(f"Multiple libraries found which match \"{library_stem}\" stem:\n{library}")
        library_paths.append(os.path.join(library[0]["base_path"], library[0]["filename"]))

    return library_paths

def find_dll_dependencies_recursively(dll_path, search_paths):
    try:
        dumpbin = subprocess.run(['dumpbin.exe', '/dependents', dll_path], capture_output=True, text=True)
        dependency_names = re.findall(r'^\s{4}(\S*\.dll)$', dumpbin.stdout, re.MULTILINE)
    except subprocess.CalledProcessError as e:
        print(f"Error running dumpbin: {e}")
        return []

    dependencies = []
    for dependency_name in dependency_names:
        for search_path in search_paths:
            dependency_path = os.path.join(search_path, dependency_name)
            if os.path.isfile(dependency_path):
                dependencies.append(dependency_path)
                found = True
                break

    dependencies_recursive = []
    for dependency in dependencies:
        dependencies_recursive.extend(find_dll_dependencies_recursively(dependency, search_paths))

    return list(set(dependencies + dependencies_recursive))

def main():
    parser = argparse.ArgumentParser(description="Find library files and their dependencies.")
    parser.add_argument('-l', '--libraries', nargs='+', required=True, help='Library base names to search for (e.g., tesseract)')
    parser.add_argument('-s', '--search-paths', nargs='+', required=True, help='Directories to search within')
    parser.add_argument('-e', '--extension', default='dll', help='File extension to match (default: dll)')
    args = parser.parse_args()

    try:
        runtime_library_paths = find_libraries(args.libraries, args.search_paths, args.extension)
        runtime_library_paths.extend(find_dll_dependencies_recursively(runtime_library_paths[0], args.search_paths))
        print(";".join(runtime_library_paths))
    except AssertionError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
