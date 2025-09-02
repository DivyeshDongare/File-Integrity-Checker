# # Driver function
# import os
# if __name__ == &quot;__main__&quot; :
#     for (root,dirs,files) in os.walk('.', topdown=True):
#         print (root)
#         print (dirs)
#         print (files)
#         print ('--------------------------------')
# import os

# def list_directory_contents(start_path='.'):
#     for root, dirs, files in os.walk(start_path, topdown=True):
#         print(f"📁 Root: {root}")
#         print(f"📂 Directories: {dirs}")
#         print(f"📄 Files: {files}")
#         print('--------------------------------')

# if __name__ == "__main__":
#     path_to_scan = '.'  # You can change this to any directory path, e.g., '/home/user/documents'
#     list_directory_contents(path_to_scan)

from pathlib import Path
from typing import List,Optional

def collect_file_paths(
        directory: str,
        include_extensions: Optional[List[str]] = None,
        exclude_hidden: int = True,
        max_depth: Optional[int] = None,
) -> List[str]:
    start_path = Path(directory).resolve()
    collected_files = []
       
