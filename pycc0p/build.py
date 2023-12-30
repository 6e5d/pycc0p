from pycparse.parse import parse_toks
from cc3py import ast2c3
from pyltr import dump, dump_flat, S
from pycprep import pycprep

def build_c(proj):
	stem = proj.stem
	includes = []
	d = proj / "build"
	toks, defines = pycprep(proj)
	j = parse_toks(toks)
	result = []
	with (
		open(d / f"{stem}.c.ast", "w") as fast,
		open(d / f"{stem}.c0", "w") as fc0,
	):
		print(dump_flat(j), file = fast)
		j = [ast2c3(jj) for jj in j]
		for jj in j:
			if jj[0] == "decfun":
				continue
			result.append(jj)
		for key, val in defines.items():
			result.append(["const", key, "int", S(val)])
		print(dump(result), file = fc0)
	return set(includes)

def step1(proj):
	cfiles = []
	for cfile in (proj / "src").iterdir():
		if cfile.name == "test.c":
			continue
		cfiles.append(cfile)
	build_c(proj)

def buildcc0(proj):
	step1(proj)
