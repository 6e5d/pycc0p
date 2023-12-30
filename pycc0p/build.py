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
	if not header.exists():
		return [], [], dict()
	d = proj / "build"
	defsu = []
	j, includes, alias = parse_project_file(str(header), proj, dict())
	with open(d / f"{stem}.h.ast", "w") as fast:
		print(dump_flat(j), file = fast)
		for jj in j:
			jj = ast2c3(jj)
			if jj[0] == "fn":
				if not jj[1].startswith(snake):
					raise Exception(jj[1], snake)
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
			jj, include, _ = parse_project_file(str(file), proj, alias)
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

def get_deps(proj):
	pgid = path2gid(proj)
	gids = [pgid]
	depfile = proj / ".lpat/deps.txt"
	if depfile.exists():
		for line in open(depfile):
			if "_" in line:
				# not c/ccc ns
				continue
			path = (proj.parent / line.strip()).resolve()
			gids.append(path2gid(path))
	sysfile = proj / ".lpat/syslib.txt"
	if sysfile.exists():
		for line in open(sysfile):
			gids.append(["com", "6e5d", "syslib"] +\
				line.strip().split("_"))
	return gids

def buildc0p(proj):
	gids = get_deps(proj)
	step1(proj)
	hasmain, links = step2(proj, gids)
	step3(proj, hasmain, links)
