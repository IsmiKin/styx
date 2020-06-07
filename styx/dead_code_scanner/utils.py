
def in_excluding_list(excluding_list, file_import):
    for excluding_pattern in excluding_list:
        if excluding_pattern in file_import:
            return True

    return False