import os
import re
import sys
import pkg_resources
from subprocess import Popen, PIPE 

def runPandocForSlides(course_config,ch,inFile):
	outFile = re.sub(r'.md$','.html',inFile)
	outFile = re.sub(r'^[0-9A-z][0-9A-z][0-9A-z][0-9A-z]-','',outFile)
	outPath = os.path.join(course_config['build_dir'],outFile)
	templateFile = os.path.join(course_config['themes_dir'],course_config['theme'],'slideshow.html')
	inPath = os.path.join(course_config['args'].dir,inFile)
	if course_config['args'].verbose:
		print '    %s => %s'%(inFile,outPath)
	cmd = 'pandoc -t html5 --template %s --standalone --section-divs \
		--mathjax=https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML \
		--variable transition="linear" %s -o %s'\
			%(templateFile,inPath,outPath)
	proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	if course_config['args'].veryverbose:
		print '    %s'%cmd 
		for line in iter(proc.stderr.readline, ''):
			print line
		proc.stdout.close()
	rc = proc.wait()
	if rc != 0:
		sys.stderr.write("Error: Something went wrong running pandoc! Quitting...\n")
		sys.stderr.write("(Use -vv for more information)\n")
		sys.exit(2)

	return outFile