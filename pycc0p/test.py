import sys, shutil
from pathlib import Path

from .build import build_c

def run_test():
	src = Path(__file__).parent.parent / "test"
	dst = Path(__file__).parent.parent / "build"
	if dst.exists():
		shutil.rmtree(dst)
	dst.mkdir()
	for file in src.iterdir():
		print(file)
		build_c([file], [], dst, file.stem)
