import os


def fix_mistakes():
    src_dir = os.path.join('data', 'source_files')

    folders = os.listdir(src_dir)

    for arxiv_id in folders:
        if not os.path.isdir(os.path.join(src_dir, arxiv_id)):
            continue

        for versionfile in os.listdir(os.path.join(src_dir, arxiv_id)):
            newfilename = f'{arxiv_id}-{versionfile}'

            with open(os.path.join(src_dir, arxiv_id, versionfile), 'rb') as fin:
                with open(os.path.join(src_dir, newfilename), 'wb') as fout:
                    fout.write(fin.read())


fix_mistakes()
