import os
import hashlib

video_dir = r"D:\AI_Projects\Swim_Analyzer_AI\data\input_videos"
hashes = {}
duplicates = {}
file_info = []

for root, dirs, files in os.walk(video_dir):
    for f in files:
        if f.endswith(".mp4"):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            h = hashlib.sha256()
            with open(fpath, "rb") as fp:
                while chunk := fp.read(8192):
                    h.update(chunk)
            digest = h.hexdigest()
            file_info.append({"filename": f, "path": fpath, "size": size, "sha256": digest})
            
            if digest in hashes:
                duplicates.setdefault(digest, [hashes[digest]]).append(f)
            else:
                hashes[digest] = f

print(f"Total files: {len(file_info)}")
print(f"Unique hashes: {len(hashes)}")
print(f"Duplicate sets: {len(duplicates)}")
for d_hash, d_files in duplicates.items():
    print(f"Hash {d_hash[:10]}... shared by ({len(d_files)} files): {d_files}")
