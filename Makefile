.PHONY: all clean

all:
	python build.py

clean:
	python -c "import os,glob; [os.remove(f) for f in glob.glob('stories/**/study.html',recursive=True)+['build/all.html'] if os.path.exists(f)]"
