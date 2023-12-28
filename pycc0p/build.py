from pycparse.parse import parse_string
from cc3py import ast2c3
from pyc0c.symbol import Symbolman
from pyc0c.translate import Translator
from pyltr import dump_flat, parse_flat
from subprocess import run as prun
from gid import path2gid, gid2c

# build_header check namespaces
# return all defs of exported structs,
# ignore fn declarations
def build_header(proj):
	gid = path2gid(proj)
	camel = gid2c(gid, "camel")
	snake = gid2c(gid, "snake")
	stem = proj.stem
	header = proj / "include" / f"{stem}.h"
	d = proj / "build"
	s = open(header).read()
	defsu = []
	with open(d / f"{stem}.h.ast", "w") as fast:
		j, includes = parse_string(s, proj)
		print(dump_flat(j), file = fast)
		for jj in j:
			jj = ast2c3(jj)
			if jj[0] == "fn":
				assert jj[1].startswith(snake)
			else:
				assert jj[1].startswith(camel)
				defsu.append(jj)
	return defsu, set(includes)

def build_c(proj, defsu):
	stem = proj.stem
	d = proj / "build"
	files = list((proj / "src").iterdir())
	includes = []
	with (
		open(d / f"{stem}.c.ast", "w") as fast,
		open(d / f"{stem}.c0", "w") as fc0,
	):
		j = []
		for file in files:
			s = open(file).read()
			jj, include = parse_string(s, proj)
			j += jj
			includes += include
		print(dump_flat(j), file = fast)
		c3s = []
		j = defsu + [ast2c3(jj) for jj in j]
		print(dump_flat(j), file = fc0)
	return set(includes)

def buildc0p1(proj):
	cfiles = []
	for cfile in (proj / "src").iterdir():
		if cfile.name == "test.c":
			continue
		cfiles.append(cfile)
	defsu, inch = build_header(proj)
	incs = build_c(proj, defsu)

def buildc0p(proj):
	buildc0p1(proj)
	stem = proj.stem
	ltr = parse_flat(open(proj / "build" / f"{stem}.c0").read())
	depfile = proj / ".lpat/deps.txt"
	gids = []
	if depfile.exists():
		for line in open(depfile):
			gids.append(path2gid(proj.parent / line))
	sm = Symbolman(gids)
	sm.analyze(ltr)
