import os
import sys
import re
import string
import nltk
from nltk import word_tokenize, pos_tag
import csv

JKFilterNounsList = ['nnp_nnp_nnp_nnp','nnp_nnp_nnp','jj_nnp_nnp','nnp_nnp_in_nnp','nnp_nnp','nnp_pr_nnp','nnp_in_nnp','jj_nnp','cd_nnp_cd','cd_nnp','nnp_cd','nnp_nnp','nnp','jj',
					 'nn_nn_nn_nn','nn_nn_nn','jj_nn_nn','nn_nn_in_nn','nn_nn','nn_pr_nn','nn_in_nn','jj_nn','cd_nn_cd','cd_nn','nn_cd','nn_nn','nn','jj'
					]        #nnx - NNP or NNS JJ CC PRP

class WordPOSTag:
	''' this class instance will be a tuple of pos tag and respective phrase
		eg. (nnp_nnp,Manjunath_Hegde)
	'''
	def __init__(self, phrase,posToken,init_flag):
		self.phrase = phrase
		if init_flag:
			posToken = self.trimPosTag(posToken.lower())
		self.posToken = posToken

	def trimPosTag(self,postag):
		if postag == 'nns':
			return 'nn'
		elif postag.startswith('nnp'):
			return 'nnp'
		else:
			return postag[:2]



inputPhrase = raw_input('input phrase: ')
words = word_tokenize(inputPhrase)
pos_tags = pos_tag(words)
# print pos_tags
pos_tag_objects = []
final_noun_phrases = {}
for w in pos_tags:
	word_pos_instance = WordPOSTag(w[0],w[1],True)
	pos_tag_objects.append(word_pos_instance)

for i in range(len(pos_tag_objects)):
	noun = ""
	pos = ""
	for j in range(0,4,1):
		if(i+j) < len(pos_tag_objects):
			cur_noun = pos_tag_objects[i+j].phrase
			cur_pos = pos_tag_objects[i+j].posToken
			noun = noun + '_' + cur_noun
			pos = pos + '_' + cur_pos
			pos = pos.strip('_')
			try:
				index = JKFilterNounsList.index(pos)
			except:
				index = -1
			#print startIndex,s,posString
			if index != -1:
				candidate_np = WordPOSTag(noun, pos, False)
				if index in final_noun_phrases:
					obj_list = final_noun_phrases.get(index)
					obj_list.append(candidate_np)
					final_noun_phrases.update({index:obj_list})
				else:
					obj_list = []
					obj_list.append(candidate_np)
					final_noun_phrases.update({index:obj_list})

key_list = final_noun_phrases.keys()
# print key_list
# print "...........NPs.........."
# print final_noun_phrases
key_list.sort()
for i in key_list:
	obj_list = final_noun_phrases.get(i)
	if len(obj_list) != 0:
		for obj in obj_list:
			print (obj.phrase).replace('_',' ')
			#print (obj.posToken).replace('_',' ')





