import os

folder_path = 'C:/Users/Administrator/Desktop/ltrs/src'  # Replace with your folder path
output_file = 'all_code_output.txt'

with open(output_file, 'w', encoding='utf-8') as out_f:
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                out_f.write(f'===== {file_path} =====\n')
                with open(file_path, 'r', encoding='utf-8') as in_f:
                    out_f.write(in_f.read())
                    out_f.write('\n\n')
print(f'All code has been written to {output_file}')
