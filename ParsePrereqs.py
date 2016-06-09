#from bs4 import BeautifulSoup

""" Parse Prerequisites """

"""
	1) Insert Tags
	2) Parse Tags
	3) create "groups" of story elements based on co-designation decisions

"""
import string
#Read document
def insertTags(file_name):
	with open(file_name) as myFile:
		#data = myFile.readlines()
		data=myFile.read().replace('\n', '')
	#for d in data:
		#print(d)
		
	string.replace(data,'(:', '<')
	string.repace(data,'steps','steps>')
	string.repace(data,'causal-links','causal-links>')
	#string.replace(data,'\n',
	print(data)
#soup = BeautifulSoup()

insertTags('danger_solution.pddl')