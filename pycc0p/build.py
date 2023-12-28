from subprocess import run as prun

from pycparse.parse import parse_string
from cc3py import ast2c3
from pyc0c.symbol import Symbolman
from pyc0c.translate import Translator
from pyltr import dump_flat, parse_flat
from pycdb.gid2file import gid2include, gid2links
from gid import path2gid, gid2c
from buildc.cc import cc

debug = False

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
	j, includes, alias = parse_string(s, proj, dict())
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
			jj, include, _ = parse_string(s, proj, alias)
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

def step2(proj):
	stem = proj.stem
	ltr = parse_flat(open(proj / "build" / f"{stem}.c0").read())
	pgid = path2gid(proj)
	gids = [pgid]
	depfile = proj / ".lpat/deps.txt"
	if depfile.exists():
		for line in open(depfile):
			gids.append(path2gid(proj.parent / line))
	sysfile = proj / ".lpat/syslib.txt"
	if sysfile.exists():
		for line in open(sysfile):
			gids.append(["com", "6e5d", "syslib"] +\
				line.strip().split("_"))
	sm = Symbolman(gids)
	sm.analyze(ltr)
	if debug:
		print("reexports:", [x[-1] for x in sm.header_includes])
		print("dependencies:", [x[-1] for x in sm.src_includes])
	d = proj / "build"
	main = False
	links = []
	with (
		open(d / f"{stem}.c", "w") as fc,
		open(d / f"{stem}.h", "w") as fh,
	):
		for gid in sm.header_includes:
			incl = gid2include(gid)
			links += gid2links(gid)
			print(f"#include {incl}", file = fh)
		for gid in sm.src_includes:
			incl = gid2include(gid)
			links += gid2links(gid)
			print(f"#include {incl}", file = fc)
		print(f'#include "{stem}.h"', file = fc)
		print(f"#pragma once", file = fh)
		t = Translator()
		for idx, b in enumerate(ltr):
			if b[1] == "main":
				main = True
			code = t.translate(b, True)
			if sm.isexports[idx]:
				print("".join(code), file = fh)
			else:
				print("".join(code), file = fc)
		for idx, b in enumerate(ltr):
			code = t.translate(b, False)
			print("".join(code), file = fc)
	return main, links

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
	print(links)
	step3(proj, hasmain, links)
