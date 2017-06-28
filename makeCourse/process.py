import sys
import os
import re
import makeCourse.pandoc

def slugify(value):
	return "".join([c for c in re.sub(r'\s+','_',value) if c.isalpha() or c.isdigit() or c=='_']).rstrip().lower()

def isHidden(obj):
	if 'hidden' in obj.keys():
		if obj['hidden']:
			return True
	return False

def createIndexYAMLheader(course_config):
	header = "---\n"
	header += "title: index\n"
	header += "author: %s\n"%course_config['author']
	header += "links:\n"
	for s in course_config['structure']:
		if isHidden(s): continue
		if s['type'] == 'part':
			header += "    - title: %s\n"%s['title']
			header += "      slug: %s\n"%slugify(s['title'])
			header += "      chapters:\n"
			for ch in s['content']:
				if isHidden(ch): continue
				header += "        -  title: %s\n"%ch['title']
				header += "           slug: %s\n"%slugify(ch['title'])
		if s['type'] == 'chapter':
			header += "    - title: %s\n"%s['title']
			header += "      slug: %s\n"%slugify(s['title'])
	header += "\n---\n\n"
	return header

def createYAMLheader(course_config,obj,part=False):
	header = "---\n"
	header += "title: %s\n"%obj['title']
	header += "author: %s\n"%course_config['author']
	if part:
		header += "part: %s\npart-slug: %s\n"%(part['title'],slugify(part['title']))
		header += "chapters:\n"
		for ch in part['content']:
			if isHidden(ch): continue
			header += "    - title: %s\n"%ch['title']
			header += "      file: %s_%s.html\n"%(slugify(part['title']),slugify(ch['title']))
			if obj == ch:
				header += "      active: 1\n"
	header +="\n---\n\n"
	return header

def createPartYAMLheader(course_config,obj):	
	header = "---\n"
	header += "title: %s\n"%obj['title']
	header += "author: %s\n"%course_config['author']
	header += "part-slug: %s\n"%(slugify(obj['title']))
	header += "chapters:\n"
	for ch in obj['content']:
		if isHidden(ch): continue
		header += "    - title: %s\n"%ch['title']
		header += "      slug: %s\n"%slugify(ch['title'])
	header += "\n---\n\n"
	return header

def buildpartMDFile(course_config,part):
	newFile = '%s-%s.md'%(os.urandom(2).encode('hex'),slugify(part['title']))
	course_config['tempFiles'].append(newFile)
	newFileContent = createPartYAMLheader(course_config,part)
	f = open(os.path.join(course_config['args'].dir,newFile), 'w')
	f.write(newFileContent)
	f.close()
	return newFile

def buildIntroMDFile(course_config,obj):
	newFile = '%s-index.md'%os.urandom(2).encode('hex')
	course_config['tempFiles'].append(newFile)
	newFileContent = createIndexYAMLheader(course_config)

	if course_config['args'].verbose:
		print 'Building index: %s'%newFile

	if obj['source'][-3:] == '.md':
		mdContents = open(os.path.join(course_config['args'].dir,obj['source']), 'r').read()
		if mdContents[:3] != '---':
			newFileContent += '\n\n' + mdContents
		else:
			sys.stderr.write("Error: Markdown file %s contains unsupported YAML header. Please remove the header, I'll make one automatically. Quitting...\n"%obj['source'])
			sys.exit(2)
	elif sec['source'][-4:] == '.tex':
		#TODO: Do latex -> html snippet
		newFileContent += '\n\n' + '# Unimplemented feature...'
	else:
		sys.stderr.write("Error: Unrecognised source type for index. Quitting...\n")
		sys.exit(2)

	f = open(os.path.join(course_config['args'].dir,newFile), 'w')
	f.write(newFileContent)
	f.close()

	if 'source' not in obj.keys():
		#TODO: latex and MD full source code for a chapter provided
		sys.stderr.write("Error: No source defined for introduction... Quitting...\n")
		sys.exit(2)

	return newFile

def buildChapterMDFile(course_config,ch,part=False):
	if 'content' in ch.keys() and 'source' in ch.keys():
			sys.stderr.write("Error: Chapter %s contains both content and source elements; including both is invalid. Quitting...\n"%ch['title'])
			sys.exit(2)

	if 'content' in ch.keys():
		if part:
			newFile = '%s-%s_%s.md'%(os.urandom(2).encode('hex'),slugify(part['title']),slugify(ch['title']))
		else:
			newFile = '%s-%s.md'%(os.urandom(2).encode('hex'),slugify(ch['title']))
		course_config['tempFiles'].append(newFile)
		newFileContent = createYAMLheader(course_config,ch,part)

		if course_config['args'].verbose:
			print 'Building chapter file: %s'%newFile

		for sec in ch['content']:
			if isHidden(sec): continue
			if sec['type'] == "section":
				if sec['source'][-3:] == '.md':
					mdContents = open(os.path.join(course_config['args'].dir,sec['source']), 'r').read()
					if mdContents[:3] != '---':
						if course_config['args'].verbose:
							print '    Adding: %s'%sec['title']
						newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\n' + mdContents
					else:
						sys.stderr.write("Error: Markdown file %s contains unsupported YAML header. Please remove the header, I'll make one automatically. Quitting...\n"%sec['source'])
						sys.exit(2)
				elif sec['source'][-4:] == '.tex':
					#TODO: Do latex -> html snippet
					newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\nUnimplemented feature...'
				else:
					sys.stderr.write("Error: Unrecognised source type for %s, %s. Quitting...\n"%(ch['title'],sec['title']))
					sys.exit(2)
			elif sec['type'] == "numbas":
				if course_config['args'].verbose:
					print '    Adding numbas iframe: %s'%sec['source']
				newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\n<iframe style="border:none;" height="1000px" width="100%" src="'+sec['source']+'"></iframe>'
			elif sec['type'] == "beamer":
				#TODO: include beamer
				newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\nUnimplemented feature...'
			elif sec['type'] == "revealjs":
				#TODO: include reveal.js
				newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\nUnimplemented feature...'
			elif sec['type'] == "vimeo":
				#TODO: include a section for a vimeo video
				newFileContent += '\n\n' + '# '+sec['title']+' {.tab-pane .fade}\n<iframe src="https://player.vimeo.com/video/'+str(sec['source'])+'" width="100%" height="360" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
			else:
				sys.stderr.write("Error: Unrecognised section type for %s, %s. Quitting...\n"%(ch['title'],sec['title']))
				sys.exit(2)

		f = open(os.path.join(course_config['args'].dir,newFile), 'w')
		f.write(newFileContent)
		f.close()

	if 'source' in ch.keys():
		if part:
			newFile = '%s-%s_%s.md'%(os.urandom(2).encode('hex'),slugify(part['title']),slugify(ch['title']))
		else:
			newFile = '%s-%s.md'%(os.urandom(2).encode('hex'),slugify(ch['title']))
		course_config['tempFiles'].append(newFile)
		newFileContent = createYAMLheader(course_config,ch,part)

		if course_config['args'].verbose:
			print 'Building chapter file: %s'%newFile

		if ch['source'][-3:] == '.md':
			mdContents = open(os.path.join(course_config['args'].dir,ch['source']), 'r').read()
			if mdContents[:3] != '---':
				if course_config['args'].verbose:
					print '    Adding: %s'%ch['title']
				newFileContent += '\n\n' + mdContents
			else:
				sys.stderr.write("Error: Markdown file %s contains unsupported YAML header. Please remove the header, I'll make one automatically. Quitting...\n"%sec['source'])
				sys.exit(2)
		elif sec['source'][-4:] == '.tex':
			#TODO: Do latex -> html snippet
			newFileContent += '\n\nUnimplemented feature...'
		else:
			sys.stderr.write("Error: Unrecognised source type for %s, %s. Quitting...\n"%(ch['title'],sec['title']))
			sys.exit(2)

		f = open(os.path.join(course_config['args'].dir,newFile), 'w')
		f.write(newFileContent)
		f.close()

	return newFile

def doProcess(course_config):
	if course_config['args'].verbose:
		print 'Exploring Structure...'

	for obj in course_config['structure']:
		if isHidden(obj): continue
		if obj['type'] == 'introduction':
			obj['title'] = 'index'
			inFileName = buildIntroMDFile(course_config,obj)
			makeCourse.pandoc.runPandocForIntro(course_config,obj,inFileName)
		elif obj['type'] == 'part':
			partFileName = buildpartMDFile(course_config,obj)
			makeCourse.pandoc.runPandocForPart(course_config,obj,partFileName)
			for ch in obj['content']:
				if(ch['type'] != 'chapter'):
					sys.stderr.write("Error: Parts must contain chapters. (%s) Quitting...\n"%obj['title'])
					sys.exit(2)
				course_config['partsEnabled'] = True
				if isHidden(obj): continue
				chFileName = buildChapterMDFile(course_config,ch,part=obj)
				makeCourse.pandoc.runPandocForChapter(course_config,ch,chFileName)
		elif obj['type'] == 'chapter':
			if course_config['partsEnabled']:
				sys.stderr.write("Error: Both parts and chapters found at top level. To fix: put all chapters inside parts or don't include parts at all. Quitting...\n")
				sys.exit(2)
			chFileName = buildChapterMDFile(course_config,ch)
			makeCourse.pandoc.runPandocForChapter(course_config,ch,chFileName)
		elif obj['type'] == 'mocktest':
			#TODO: build a mock test numbas page!
			sys.stderr.write("Error: Unimplemented feature... Quitting...\n")
			sys.exit(2)

	if course_config['args'].verbose:
		print 'Done!'