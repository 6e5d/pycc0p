from subprocess import run as prun

from pycparse.parse import parse_project_file
from cc3py import ast2c3
from pyltr import dump_flat
from gid import path2gid, gid2c
from buildc.cc import cc
from .step2 import step2

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
	j, includes, alias = parse_project_file(s, proj, dict())
	with open(d / f"{stem}.h.ast", "w") as fast:
		print(dump_flat(j), file = fast)
		for jj in j:
			jj = ast2c3(jj)
			if jj[0] == "fn":
				assert jj[1].startswith(snake)
			else:
				assert jj[1].startswith(camel)
				defsu.append(jj)
	return defsu, set(includes), alias

def build_c(proj, defsu, alias):
	stem = proj.stem
	files = list((proj / "src").iterdir())
	includes = []
	d = proj / "build"
	with (
		open(d / f"{stem}.c.ast", "w") as fast,
		open(d / f"{stem}.c0", "w") as fc0,
	):
		j = []
		for file in files:
			s = open(file).read()
			jj, include, _ = parse_project_file(s, proj, alias)
			j += jj
			includes += include
		print(dump_flat(j), file = fast)
		c3s = []
		j = defsu + [ast2c3(jj) for jj in j]
		print(dump_flat(j), file = fc0)
	return set(includes)

def step1(proj):
	cfiles = []
	for cfile in (proj / "src").iterdir():
		if cfile.name == "test.c":
			continue
		cfiles.append(cfile)
	defsu, inch, alias = build_header(proj)
	incs = build_c(proj, defsu, alias)

def step3(proj, hasmain, links):
	stem = proj.stem
	d = proj / "build"
	cmd = cc()
	if hasmain:
		cmd += ["-fPIE", "-o", d / f"{stem}.elf"]
	else:
		cmd += ["-fPIC", "-shared", "-o", d / f"lib{stem}.so"]
	cmd += links
	cmd.append(d / f"{stem}.c")
	prun(cmd, check = True)

def buildc0p(proj):
	step1(proj)
	hasmain, links = step2(proj)
	step3(proj, hasmain, links)
