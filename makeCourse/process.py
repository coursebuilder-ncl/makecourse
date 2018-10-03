import logging
from . import hackmd
from . import latex
from . import pandoc
from . import plastex
from .item import load_item
import os
import re
import sys
from makeCourse import *

logger = logging.getLogger(__name__)

class CourseProcessor:

	def temp_path(self, path):
		tmp_dir = 'tmp'
		if not os.path.exists(tmp_dir):
			os.makedirs(tmp_dir)
		tpath = None
		while tpath is None or os.path.exists(tpath):
			tpath = os.path.join(tmp_dir,'{}-{}'.format(os.urandom(2).encode('hex'),path))
		self.config['tempFiles'].append(tpath)
		return tpath

	def replaceLabels(self,mdContents):
		for l in gen_dict_extract('label',self.config):
			mdLink = re.compile(r'\[([^\]]*)\]\('+l['label']+r'\)')
			mdContents = mdLink.sub(lambda m: "[" + m.group(1)+"]("+self.config['web_root']+l['outFile']+".html)", mdContents)
		return mdContents

	def getVimeoHTML(self, code):
		return '<iframe src="https://player.vimeo.com/video/'+code+'" width="100%" height="360" frameborder="0" \
				webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
	def getRecapHTML(self, code):
		return '<iframe src="https://campus.recap.ncl.ac.uk/Panopto/Pages/Embed.aspx?id='+code+'&v=1" width="100%" \
				height="640" frameborder="0" gesture=media webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
	def getYoutubeHTML(self, code):
		return '<iframe width="100%" height="360" src="https://www.youtube.com/embed/'+code+'?ecver=1" frameborder="0" allowfullscreen></iframe>'
	def getNumbasHTML(self, URL):
		return '<iframe width="100%" height="1000px" src="'+URL+'" frameborder="0"></iframe>'
	def getSlidesHTML(self, code):
		hackmd.getSlidesPDF(self.config,code)
		return '<iframe src="'+HACKMD_URL+'/p/'+code+'/" style="overflow:hidden;" width="100%" height="480px" scrolling=no frameborder="0">\
				</iframe><div class="pad-top-10 pull-right"><a href="'+self.config['web_root']+'static/'+code+'.pdf"><i class="fa fa-file-pdf-o" aria-hidden="true"></i> Download</a> \
				|&nbsp;<a target="_blank" href="'+HACKMD_URL+'/p/'+code+'/"><i class="fa fa-arrows-alt" aria-hidden="true"></i> Fullscreen</a></div>'
	def getSlidesURL(self,code):
		hackmd.getSlidesPDF(self.config,code)
		return HACKMD_URL+'/p/'+code+'/'

	def burnInExtras(self,mdContents,force_local,out_format):
		mdContentsOrig = mdContents
		reVimeo = re.compile(r'{%vimeo\s*([\d\D]*?)\s*%}')
		reRecap = re.compile(r'{%recap\s*([\d\DA-z-]*?)\s*%}')
		reYoutube = re.compile(r'{%youtube\s*([\d\D]*?)\s*%}')
		reNumbas = re.compile(r'{%numbas\s*([^%{}]*?)\s*%}')
		reSlides = re.compile(r'{%slides\s*([^%{}]*?)\s*%}')
		if out_format=='pdf':
			mdContents = reVimeo.sub(lambda m: "\n\n\url{https://vimeo.com/"+m.group(1)+"}", mdContents)
			mdContents = reRecap.sub(lambda m: "\n\n\url{https://campus.recap.ncl.ac.uk/Panopto/Pages/Viewer.aspx?id="+m.group(1)+"}", mdContents)
			mdContents = reYoutube.sub(lambda m: "\n\n\url{https://www.youtube.com/watch?v="+m.group(1)+"}", mdContents)
			mdContents = reNumbas.sub(lambda m: "\n\n\url{"+m.group(1)+"}", mdContents)
			mdContents = reSlides.sub(lambda m: "\n\n\url{"+self.getSlidesURL(m.group(1))+"}", mdContents)
		else:
			mdContents = reVimeo.sub(lambda m: self.getVimeoHTML(m.group(1)), mdContents)
			mdContents = reRecap.sub(lambda m: self.getRecapHTML(m.group(1)), mdContents)
			mdContents = reYoutube.sub(lambda m: self.getYoutubeHTML(m.group(1)), mdContents)
			mdContents = reNumbas.sub(lambda m: self.getNumbasHTML(m.group(1)), mdContents)
			mdContents = reSlides.sub(lambda m: self.getSlidesHTML(m.group(1)), mdContents)

		if force_local:
			relativeImageDir = self.config['local_root']+"static/"
		else:
			relativeImageDir = self.config['web_root']+"static/"

		logger.info("    Webize images: replacing './build/static/' with \""+relativeImageDir+"\" in paths.")
		mdContents = mdContents.replace('./build/static/', relativeImageDir)

		if mdContents != mdContentsOrig:
			logger.debug('    Embedded iframes & extras.')
		mdContents = self.replaceLabels(mdContents)
		return mdContents

	def makePDF(self,item):
		_, ext = os.path.splitext(item.source)
		if ext == '.tex':
			latex.runPdflatex(self,item)
		elif item.type == 'slides':
			self.run_decktape(item)
		else:
			self.run_pandoc(item,template_file='notes.latex', out_format='pdf',force_local=True)

	def doProcess(self):
		logger.info('Preprocessing Structure...')
		self.structure = [load_item(self,obj) for obj in self.config['structure']]

		logger.info('Deep exploring Structure...')

		for obj in self.structure:
			if obj.is_hidden:
				continue
			if obj.type == 'introduction':
				logger.info('Building Index file index.html')
				self.run_pandoc(obj)

			elif obj.type == 'part':
				mkdir_p(os.path.join(self.config['build_dir'],obj.out_file))
				self.run_pandoc(obj)
				for chapter in obj.content:
					if(chapter.type == 'chapter'):
						logger.info('Building chapter: {}'.format(chapter.title))
						self.config['partsEnabled'] = True
						if chapter.is_hidden:
							continue
						self.run_pandoc(chapter)
						if self.config["build_pdf"]:
							self.makePDF(chapter)
					elif(chapter.type == 'recap'):
						logger.info('Building recap: {}'.format(chapter.title))
						self.config['partsEnabled'] = True
						if chapter.is_hidden:
							continue
						self.run_pandoc(chapter)
					elif(chapter.type == 'url'):
						self.config['partsEnabled'] = True
						if chapter.is_hidden:
							continue
					elif(chapter.type == 'slides'):
						logger.info('Building slides: {}'.format(chapter.title))
						self.config['partsEnabled'] = True
						if chapter.is_hidden:
							continue
						self.run_pandoc(chapter)
						self.run_pandoc(chapter,template_file='slides.revealjs',out_format='slides.html',force_local=True)
						if self.config["build_pdf"]:
							self.makePDF(chapter)
						if not self.args.local:
							self.run_pandoc(chapter,template_file='slides.revealjs',out_format='slides.html')
					else:
						raise Exception("Error: Unsupported chapter type! {} is a {}".format(chapter.title, chapter.type))
			else:
				if obj.is_hidden:
						continue
				if self.config['partsEnabled']:
					raise Exception("Error: Both parts and chapters found at top level. To fix: put all chapters inside parts or don't include parts at all. Quitting...\n")
				if obj.type == 'chapter':
					logger.info('Building chapter: {}'.format(obj.title))
					self.run_pandoc(obj)
					if self.config["build_pdf"]:
							self.makePDF(obj)
				elif obj.type == 'recap':
					logger.info('Building recap: {}'.format(obj.title))
					self.run_pandoc(obj)
				elif obj.type == 'slides':
					logger.info('Building slides: {}'.format(obj.title))
					self.run_pandoc(obj)
					self.run_pandoc(obj,template_file='slides.revealjs',out_format='slides.html',force_local=True)
					if self.config["build_pdf"]:
						self.makePDF(obj)
					self.run_pandoc(obj,template_file='slides.revealjs',out_format='slides.html')

		logger.info('Done!')