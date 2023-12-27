from pycparse.parse import parse_string
from cc3py import ast2c3
from pyltr import dump_flat
from subprocess import run as prun

def build_header(proj):
	stem = proj.stem
	header = proj / "include" / f"{stem}.h"
	d = proj / "build"
	exports = []
	with (
		open(d / f"{stem}.h0", "w") as fh0,
		open(d / f"{stem}.ast", "w") as fast,
	):
		s = open(header).read()
		j, includes = parse_string(s, proj)
		for jj in j:
			jj = ast2c3(jj)
			print(dump_flat(jj), file = fh0)
	return exports

def build_c(proj):
	stem = proj.stem
	d = proj / "build"
	files = list((proj / "src").iterdir())
	with (
		open(d / f"{stem}.ast", "w") as fast,
		open(d / f"{stem}.c0", "w") as fc0,
	):
		j = []
		for file in files:
			s = open(file).read()
			jj, includes = parse_string(s, proj)
			j += jj
		print(dump_flat(j), file = fast)
		c3s = []
		j = [ast2c3(jj) for jj in j]
		print(dump_flat(j), file = fc0)

def buildc0p(proj):
	cfiles = []
	for cfile in (proj / "src").iterdir():
		if cfile.name == "test.c":
			continue
		cfiles.append(cfile)
	exports = build_header(proj)
	build_c(proj)
