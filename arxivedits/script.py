from arxivedits import data
import os, shutil
import tqdm

root = "/Users/samstevens/Dropbox/arXiv_edit_Sam_Chao/Sam_working_folder/arxivedits"

datapath = os.path.join(root, "data")
downloadpath = os.path.join(root, "arxiv-downloads")


def script() -> None:

    ids = set([data.id_to_path(a) for a, v in data.get_sample_files()])
    print(len(ids))

    for d in tqdm.tqdm(os.listdir(datapath)):
        d = data.id_to_path(d)
        oldpath = os.path.join(datapath, d)
        newpath = os.path.join(downloadpath, d)

        if d in ids:
            # print(f"moving {d} from {oldpath} to {newpath}")
            shutil.move(oldpath, newpath)
            ids.remove(d)

    print(ids)


if __name__ == "__main__":
    script()
