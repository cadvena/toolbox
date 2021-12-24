import re
# from toolbox import tb_cfg


# defining the replace method
def replace_in_file(file_path, regex_string, replace_with):
    # open the file
    with open (file_path, "r+") as file:
        # read the file contents
        file_contents = file.read ()
        text_pattern = re.compile (regex_string)
        file_contents = text_pattern.sub (replace_with, file_contents)
        file.seek (0)
        file.truncate ()
        file.write (file_contents)

