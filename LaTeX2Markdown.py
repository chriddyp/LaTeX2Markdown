"""
Simple LaTeX to Markdown converter
"""
import re
import sys
import os

####################################################################################
############################### Conversion Functions ############################### 
####################################################################################

############################### Conversion A ############################### 
# Replace and wrap, e.g.:  \part{string} -> #string#
def Tex2MarkDicAConv(instr, Tex2MarkDicA):
	outstr = instr
	for t,m in Tex2MarkDicA.iteritems():
		p = re.compile( "\\\\" + t	+		# match tex tag, e.g. \part...
					"[\*]?" +			# or \part*
					"\{ ( [^}]* ) \}",	# with anything inside curly braces, ...
										# except for curly braces: \part{str} ... 
										# not \part{str1} \section{str2}
										# ( ) is group notation, used below
					re.DOTALL | re.VERBOSE)		# re.DOTALL: incl newline with (.)
		# perform t2m replace, eg \part{str} to #{str}#
		outstr = p.sub(m + '\\1' + m, outstr) # where \1 pulls the text, ...
												# (\\ needed since for raw str) ...
												# found inside the group ( ) from above	
	return outstr
	
############################### Conversion B ############################### 
# Wrap, e.g. \begin{eqnarray} string \end{eqnarray} -> $$\begin{eqnarray} string \end{eqnarray}$$
def Tex2MarkDicBConv(instr, Tex2MarkDicB):
	outstr = instr
	for t,m in Tex2MarkDicB.iteritems():
		""" Usage:
		teststr = "\\begin{eqnarray*} blah \\end{eqnarray*})"
		teststr = teststr.replace('\\begin{' + t + '*}', '$$\\begin{' + t + '*}')
		teststr = teststr.replace('\\end{' + t + '}', '\\end{' + t + '}$$') 
		"""
		outstr = outstr.replace('\\begin{' + t + '*}', '$$ \\begin{' + t + '*}')
		outstr = outstr.replace('\\end{' + t + '*}', '\\end{' + t + '*} $$')
		outstr = outstr.replace('\\begin{' + t + '}', '$$ \\begin{' + t + '}')
		outstr = outstr.replace('\\end{' + t + '}', '\\end{' + t + '} $$')	
	return outstr

############################### Conversion C ############################### 
# Simple find and replace. e.g. \item -> *
def Tex2MarkDicCConv(instr, Tex2MarkDicC):
	outstr = instr
	for t,m in Tex2MarkDicC.iteritems():
		outstr = outstr.replace(t, m)
	return outstr
	

############################### Convert Table ############################### 
def table_conv(instr):
	## Get header tags for each table
	pheader = re.compile("""\\\\begin\{tabular\}
						\{
						([^ \}]* )
						\}""",
						re.VERBOSE)

	## split text into segments containing or not containing tables
	ptable = re.compile("""
						(\\\\begin\{tabular\}
						.*?
						\\\\end\{tabular\})
						""",
						re.DOTALL | re.VERBOSE)
						

	splitstr = ptable.split(instr)

	i = 0
	for table_i in splitstr:
		# If there is one table in one of the strings 
		# (the regex above should've split the text 
		# such that there is only one table in each split string
		table_i_exist = table_i.count('\\begin{tabular}')
		if table_i.count('\\begin{tabular}') > 1:
			print """ERROR: Table conversion Error 1"""
		elif table_i.count('\\begin{tabular}') == 1:
			colstr = pheader.findall(table_i)
			if len(colstr) > 1:
				print "Error: Something wrong with number of columns"
			num_col = colstr[0].count('|c') 	#number of columns for this table

			# Build string to replace \hline #
			mark_col = []
			for ii in xrange(num_col):
				mark_col.append('---|')
			mark_col = ''.join(mark_col)
			mark_col = mark_col.strip('|')
			# delete first \hline (hline exists between firstline and \begin{tabular}
			table_i_rep = table_i.replace('\\hline', '', 1) 
			# replace the next \hline with markdown's header/cell divider
			table_i_rep = table_i_rep.replace('\\hline', mark_col, 1)
			# delete the remaining \hlines - assuming \hline is the divder between new cell rows
			table_i_rep = table_i_rep.replace('\\hline \n', '') 
			# replace the column dividers (&) with markdown column dividers (|)	...
			# ... but don't replace \& 
			table_i_rep = re.sub('[^\\\\]&', '|', table_i_rep)
			# table_i_rep = table_i_rep.replace('\&', '')

			splitstr[i] = table_i_rep
		i+=1
	markstr = ''.join(splitstr)
	markstr = pheader.sub('', markstr)
	return markstr

############################### Conversion D ############################### 
# Replace strings only if they are between \begin{environment} and \end{environment} tags
# e.g. replace \hline with '' only if it within the \begin{tabular} and \end{environment} tags
def Tex2MarkDicDConv(instr, Tex2MarkDicD):
	for t,m in Tex2MarkDicD.iteritems():
		## split text into segments containing or not containing tables
		penv = re.compile("""
							(\\\\begin\{""" + t + """\}
							.*?
							\\\\end\{""" + t + """\})
							""",
							re.DOTALL | re.VERBOSE)
	
		splitstr = penv.split(instr)
		i = 0
		for env_i in splitstr:	
			# If there is an environment in one of the strings 
			# (the regex above should've split the text 
			# such that there is only one environment in each split string)
			if env_i.count('\\begin{' + t + '}') > 1:
				print """ERROR: D conversion Error 1"""
			elif env_i.count('\\begin{' + t + '}') == 1:
				for tnest, mnest in m.iteritems():
					env_i = env_i.replace(tnest, mnest)
				splitstr[i] = env_i
			i+=1
		markstr = ''.join(splitstr)
	return markstr
	

####################################################################################
################################### Main Script #################################### 
####################################################################################


############################ Conversion Dictionaries ############################### 
# 	Tex 2 Markdown Dictionary A:
#	replace, eg, \part{str} with #str#
# 	i.e. keyword at begining and brackets surrounding string, ...
# 	and replace with keywords surrounding string
Tex2MarkDicA = {'part': '#',		\
				'section': '##',	\
				'subsection': '###',\
				'paragraph': '####',\
				'textbf': '**',\
				'emph': '*',\
				'caption': '*', \
				}

# 	Tex 2 Markdown Dictionary B: begin/end insertion
#	insert, e.g., $$ around, e.g., ....
#	\begin{eqnarray} text \end{eqnarray}
Tex2MarkDicB = {'eqnarray': "$$"}


#	Tex 2 Markdown Dictionary C: 
# 	Simple find and replace, ...
# 	e.g. \item -> * 

# Assuming that these characters will never be written on their own ,...
# i.e. no one will actually write '\_' 
Tex2MarkDicC = {'\\item ': '* ', \
				'\\begin{itemize}': '', \
				'\\end{itemize}': '', \
				'\\begin{tabular}': '', \
				'\\end{tabular}': '' , \
				'\\begin{table}': '', \
				'\\end{table}': '' , \
				'\\begin{minipage}': '\n***\n', \
				'\\end{minipage}': '\n***\n', \
				'\\framebox{': '', \
				'\\&': '&', \
				'\\#': '#', \
				'\\$': '$', \
				'\\%': '%', \
				'\\textasciicircum{}': '^', \
				'{*}': '*', \
				'\_': '_', \
				'{[}': '[', \
				'{]}': ']', \
				'\\{': '{', \
				'\\}': '}', \
				'\\textbackslash{}': '\\', \
				'\\textasciitilde{}': '~' \
				}

#	Tex 2 Markdown Dictionary D: 
# 	find and replace within environments ...
# 	e.g. \item -> * 
Tex2MarkDicD = {'tabular': {'\\tabularnewline': '', \
							}
				}
	
################################################################################################
# Read  the File ###############################################################################
################################################################################################
filename = raw_input("Enter tex file name: ")
f = open(filename)
fstr = f.read()				#entire file is 1 string

################################################################################################
# Text conversions #############################################################################
################################################################################################
## Step 1: Copy everything between \begin{document} and \end{document} ##
p = re.compile("""
				\\\\begin{document}			# match \begin{document}
				(.*)						# ... and everything before
				\\\\end{document}"""		# \end{document}
				,re.DOTALL | re.VERBOSE)		# re.DOTALL: incl newline with (.)
marklist = p.findall(fstr)
if(len(marklist) == 1):
	markstr = marklist[0]
else:
	sis.exit("Error: Found more than 1 \\begin{documents}. Quitting.")

## Step 2: 	Call the conversion methods
markstr = Tex2MarkDicDConv(markstr, Tex2MarkDicD)
markstr = table_conv(markstr)
markstr = Tex2MarkDicAConv(markstr, Tex2MarkDicA)
markstr = Tex2MarkDicBConv(markstr, Tex2MarkDicB)
markstr = Tex2MarkDicCConv(markstr, Tex2MarkDicC)
#markstr = Tex2MarkDicEConv(markstr)

markstr = "*** \n *** \n##This text was generated using a very simple LaTeX to Markdown converter." + \
			" Please check the text for LaTeX to Markdown translation errors before you publish. Thanks!.##" + \
			"\n *** \n *** \n""" + markstr 
print '###########################################################'
print '############## LATEX2MARKDOWN CONVERSION ##################'
print '###########################################################'

print markstr	
				
					
					
					
					
					
					
					
