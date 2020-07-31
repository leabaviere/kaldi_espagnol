#donner en argument 1 le nom du fichier nettoyé (ex: cleaned_le_monde)

import os
import codecs
import bz2
from unicodedata import normalize
#import unicode
from sys import argv
import re
import sys
from num2words import num2words
from lxml import etree
from xml.etree import ElementTree
import tarfile
from tqdm import tqdm
import string
import inflect
from unidecode import unidecode
import io
import spacy
import numpy as np
from spacy import displacy
from spacy.lang.es.examples import sentences
from spacy.pipeline import SentenceSegmenter
from spacy.pipeline import Tagger
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token
import logging

#vocabulaire de tg_sphinx
tg_sphinx = ""
with open("vocab-full.txt", "r", encoding="utf-8") as text_file:
    tg_sphinx = text_file.read()
    tg_sphinx = tg_sphinx.replace("- ","")
    tg_sphinx = re.split(r'\n', tg_sphinx)

#initilization of the text corpora
corpus = ""

print("processing data...")
#A MODIFIER
corpus = ""
list_punct = tuple(list(string.punctuation))
for text in tg_sphinx:
    if(not text.startswith(list_punct)):
        text = text.replace("\r"," ")
        text = text.replace("\n"," ")
        text = text.replace("\r\n"," ")
        text = text.replace(">"," ")
        text = text.replace("<"," ")
        text = text.replace("_"," ")
        text = text.replace("/"," ")
        text = text.replace("¹"," ")
        text = text.replace("²"," cuadrado")
        text = text.replace("³"," cubo")
        text = text.replace("⁴"," ")
        text = text.replace('°'," grados")
        text = text.replace('–',"-")
        text = text.replace("’","'")
        text = text.replace("A ","à ")
        text = " ".join(text.split())
        #removing whitespace and punctuation at the beginning
        text = re.sub(r"^[ \"'\_:.!?\\-]{1,}"," ",text)
        corpus += text+"\n"
                
#we write corpus string in a file
with open("n_vocab-full.txt", "w", encoding="utf-8") as text_file:
    text_file.write(corpus)

def split_on_breaks(doc):
    start = 0
    seen_break = False
    for word in doc:
        if seen_break:
            yield doc[start:word.i-1]
            start = word.i
            seen_break = False
        elif word.text in ["\n"]:
            seen_break = True
    if start < len(doc):
        yield doc[start:len(doc)]

#découpage en phrases selon la ponctuation forte, ainsi que les ":" ou les parenthèses
def split_on_breaks2(doc):
    start = 0
    start_brackets = []
    end_brackets = []
    seen_break = False
    seen_brackets = False
    for word in doc:
        if seen_break:
            if not seen_brackets:
                yield doc[start:word.i]
                #yield doc[start:word.i-1]
                start = word.i
                seen_break = False
            elif seen_brackets and end_brackets and start_brackets:
                concatene = str(doc[start:start_brackets[0]])+" "
                for j in range(min(len(start_brackets)-1,len(end_brackets)-1)):
                    concatene += str(doc[end_brackets[j]+1:start_brackets[j+1]])+" "
                #concatene += str(doc[end_brackets[-1]+1:word.i-1])
                concatene += str(doc[end_brackets[-1]+1:word.i])
                yield nlp.make_doc(concatene)[:]
                start = word.i
                start_brackets = []
                end_brackets = []
                seen_brackets = False
                seen_break = False
        elif word.text in ["...",".",":","?","!"]:
            seen_break = True
        elif word.text == "(":
            seen_brackets = True
            start_brackets.append(word.i)
        elif word.text == ")" and start_brackets:
            end_brackets.append(word.i)
            yield doc[start_brackets[-1]+1:word.i]
    if start < len(doc):
        if not seen_brackets:
            #yield doc[start:len(doc)-1]
            yield doc[start:len(doc)]
        elif seen_brackets and end_brackets and start_brackets:
            concatene = str(doc[start:start_brackets[0]])+" "
            for j in range(min(len(start_brackets)-1,len(end_brackets)-1)):
                concatene += str(doc[end_brackets[j]+1:start_brackets[j+1]])+" "
            #concatene += str(doc[end_brackets[-1]+1:len(doc)-1])
            concatene += str(doc[end_brackets[-1]+1:len(doc)])
            yield nlp.make_doc(concatene)[:]

def clean_component(doc): 
    output = []
    for sent in doc.sents:
        for token in sent:
            if not token.is_punct:
                output.append(token.text)
        output.append("\n")
    output = " ".join(output)
    return(nlp.make_doc(output))


#solution simple pour le moment, on les supprime
def treat_url_and_email(doc):
    pattern_url = [{'LIKE_URL': True}]
    pattern_email = [{'LIKE_EMAIL': True}]
    matcher = Matcher(doc.vocab)
    matcher.add('URL', None, pattern_url)
    matcher.add('EMAIL', None, pattern_email)
    matches = matcher(doc)
    spans = []
    start = 0
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        start = end_match
    if(start<len(doc)):    
        spans.append(doc[start:].text)
    spans = " ".join(spans)
    doc = nlp.make_doc(spans)
    return(doc)


#fonction utiliser dans roman_numbers qui transforme les chiffres romains en nombres
def roman_to_int(s):
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]
    return(str(int_val))


#transformer les chiffres romains
def roman_numbers(doc):
    pattern1 = [{'ORTH': "I"}]   
    pattern2 = [{'ORTH': "II"}]
    pattern3 = [{'ORTH': "III"}]
    pattern4 = [{'ORTH': "IV"}]
    pattern5 = [{'ORTH': "V"}]
    pattern6 = [{'ORTH': "VI"}]
    pattern7 = [{'ORTH': "VII"}]
    pattern8 = [{'ORTH': "VIII"}]
    pattern9 = [{'ORTH': "IX"}]
    pattern10 = [{'ORTH': "X"}]
    pattern11 = [{'ORTH': "XI"}]
    pattern12 = [{'ORTH': "XII"}]
    pattern13 = [{'ORTH': "XIII"}]
    pattern14 = [{'ORTH': "XIV"}]
    pattern15 = [{'ORTH': "XV"}]
    pattern16 = [{'ORTH': "XVI"}]
    pattern17 = [{'ORTH': "XVII"}]
    pattern18 = [{'ORTH': "XVIII"}]
    pattern19 = [{'ORTH': "XIX"}]
    pattern20 = [{'ORTH': "XX"}]
    pattern21 = [{'ORTH': "XXI"}]
    
    matcher = Matcher(doc.vocab)
    
    matcher.add("format_pattern1", None, pattern1)
    matcher.add("format_pattern2", None, pattern2)
    matcher.add("format_pattern3", None, pattern3)
    matcher.add("format_pattern4", None, pattern4)
    matcher.add("format_pattern5", None, pattern5)
    matcher.add("format_pattern6", None, pattern6)
    matcher.add("format_pattern7", None, pattern7)
    matcher.add("format_pattern8", None, pattern8)
    matcher.add("format_pattern9", None, pattern9)
    matcher.add("format_pattern10", None, pattern10)
    matcher.add("format_pattern11", None, pattern11)
    matcher.add("format_pattern12", None, pattern12)
    matcher.add("format_pattern13", None, pattern13)
    matcher.add("format_pattern14", None, pattern14)
    matcher.add("format_pattern15", None, pattern15)
    matcher.add("format_pattern16", None, pattern16)
    matcher.add("format_pattern17", None, pattern17)
    matcher.add("format_pattern18", None, pattern18)
    matcher.add("format_pattern19", None, pattern19)
    matcher.add("format_pattern20", None, pattern20)
    matcher.add("format_pattern21", None, pattern21)
    
    matches = matcher(doc)
    
    start = 0
    spans = []
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        if(doc[start_match].text[-1]=="e"):
            value_to_convert = doc[start_match].text[:-1]
        else:
            value_to_convert = doc[start_match].text
        spans.append(roman_to_int(value_to_convert))
        start = end_match        
    if(start<len(doc)):
        spans.append(doc[start:].text)
    output = " ".join(spans)    
    return(nlp.make_doc(output))



#transformer les formules du type : 1er => premier, 2ème => deuxième...
def ordinal_numbers(doc):
    #on matche toutes les expressions de la forme "12e, 1er, ..."
    pattern = re.compile(r'([0-9]+)(?:er|°)')
    start = 0
    spans = []
    #for match in re.finditer(pattern, doc.text):
    for match in re.finditer(pattern, doc.text):
        start_match, end_match = match.span()
        text_add = doc.char_span(start_match, end_match)
        if(text_add is not None):
            spans.append(doc[start:start_match].text)
            #dans l'expression matché "pattern", on récupère que les digits
            number = int("".join(re.findall('\\d+', str(text_add))))
            spans.append(num2words(number, to='ordinal', lang='es'))
            start = end_match 
    if(start<len(doc)):
        spans.append(doc[start:].text)
    output = " ".join(spans)    
    return(nlp.make_doc(output))



#transformer les floats (8.1 devient 8 virgule 1)
def treat_floats(doc):
    patterns = pattern = [{'LIKE_NUM': True}]
    matcher = Matcher(doc.vocab)
    matcher.add("treat_float", None, patterns)
    spans = []
    matches = matcher(doc) 
    start = 0   
    sent_span = []
    for match_id, start_match, end_match in matches:
        if("." in doc[start_match].text):
            spans.append(doc[start:start_match].text)
            spans.append(doc[start_match:end_match].text.replace("."," point "))
            start = end_match
        elif("," in doc[start_match].text):
            spans.append(doc[start:start_match].text)
            spans.append(doc[start_match:end_match].text.replace(","," virgule "))
            start = end_match
    if(start<len(doc)):
        spans.append(doc[start:].text)
    spans = " ".join(spans)
    doc = nlp.make_doc(spans)
    return(doc)


def treat_bad_digits(doc):
    patterns = [{'IS_DIGIT': True, 'OP': '+'},
           {'IS_SPACE': True, 'OP': '?'},
           {'IS_DIGIT': True, 'OP': '+'}]
    matcher = Matcher(doc.vocab)
    matcher.add("format_number", None, patterns)
    spans = []
    matches = matcher(doc) 
    start = 0   
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        spans.append(doc[start_match:end_match].text.replace(" ",""))
        start = end_match
    if(start<len(doc)):    
        spans.append(doc[start:].text)
    spans = " ".join(spans)
    #corriger bug si la fin de phrase est un nombre
    doc = nlp.make_doc(spans)
    return(doc)


def treat_dates(doc):
    pattern1 = [{'SHAPE': 'dddd'},
           {'IS_PUNCT': True},
           {'SHAPE': 'dddd'}]
    matcher = Matcher(doc.vocab)
    matcher.add('DATE', None, pattern1)
    matches = matcher(doc)
    spans = []
    start = 0
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        spans.append(doc[start_match:end_match].text[:4]+" "+doc[start_match:end_match].text[-4:])
        start = end_match
    if(start<len(doc)):    
        spans.append(doc[start:].text)
    spans = " ".join(spans)
    doc = nlp.make_doc(spans)
    return(doc)

def treat_phone_numbers(doc):
    pattern = [{'SHAPE': 'dd­dd­dd­dd­dd'}]
    matcher = Matcher(doc.vocab)
    matcher.add('PHONE_NUMBER', None, pattern)
    matches = matcher(doc)
    spans = []
    start = 0
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        spans.append(doc[start_match].text[0]+" "+doc[start_match].text[1])
        spans.append(doc[start_match:end_match].text[3:].replace("­"," "))
        start = end_match
    if(start<len(doc)):    
        spans.append(doc[start:].text)
    spans = " ".join(spans)
    #corriger bug si la fin de phrase est un nombre
    doc = nlp.make_doc(spans)
    return(doc)


def digits_to_words(doc):
	output = []
	p = inflect.engine()
	for token in doc:
		if(token.is_digit):
			try:
				output.append(num2words(int(token.text), lang='es'))
			except (ValueError):
				pass
		else:
			output.append(token.text)
	output = " ".join(output)
	doc = nlp.make_doc(output)
	return(doc)


def filter_punctuation(doc):
    pattern_comma = [{'ORTH': ',', 'OP': '+'}]
#ORTH : The exact verbatim of a token ; OP : Require the pattern to match 1 or more times
    pattern_arobas = [{'ORTH': '@', 'OP': '+'}]
    pattern_gui = [{'ORTH': '"', 'OP': '+'}]
    pattern_gui2 = [{'ORTH': '«', 'OP': '+'}]
    pattern_gui3 = [{'ORTH': '»', 'OP': '+'}]
    
    matcher = Matcher(doc.vocab)
    
    matcher.add("remove_comma", None, pattern_comma)
    matcher.add("remove_arobas", None, pattern_arobas)
    matcher.add("remove_gui", None, pattern_gui)
    matcher.add("remove_gui2", None, pattern_gui2)
    matcher.add("remove_gui3", None, pattern_gui3)
    
    matches = matcher(doc)
    spans = []
    start = 0
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        start = end_match
    #corriger bug si la fin de phrase est un nombre
    if(start<len(doc)):
        spans.append(doc[start:].text)
    output = " ".join(spans)
    return(nlp.make_doc(output))



def replace_expressions(doc):
    pattern1 = [{'LOWER': 'sr.'}]
    pattern1_bis1 = [{'LOWER': 'sr'}]
    pattern1_bis2 = [{'LOWER': 'srs'}]
    pattern1_bis3 = [{'LOWER': 'srs.'}]
    pattern2 = [{'ORTH': "%"}]
    pattern3 = [{'IS_SPACE': True}]
    pattern4 = [{'ORTH': "+"}]
    pattern5 = [{'ORTH': "h"}]
    pattern6 = [{'LOWER': "sra"}]
    pattern6_bis1 = [{'LOWER': "sra."}]
    pattern6_bis2 = [{'LOWER': "sras"}]
    pattern6_bis3 = [{'LOWER': "sras."}]
    pattern7 = [{'ORTH': "="}]
    pattern8 = [{'ORTH': "&"}]
    pattern9 = [{'ORTH': "`"}]
    pattern10 = [{'ORTH': "f"}]
    pattern11 = [{'ORTH': "e"}]
    pattern12 = [{'ORTH': "m"}]
    pattern13 = [{'LOWER': 'vd.'}]
    pattern13_bis1 = [{'LOWER': 'vds.'}]
    pattern13_bis2 = [{'LOWER': 'vd'}]
    pattern13_bis3 = [{'LOWER': 'vds'}]
    pattern14 = [{'LOWER': 'dr'}]
    pattern14_bis1 = [{'LOWER': 'dr.'}]
    pattern15 = [{'LOWER': 'dra'}]
    pattern15_bis1 = [{'LOWER': 'dra.'}]
    pattern16 = [{'LOWER': "srta"}]
    pattern16_bis1 = [{'LOWER': "srta."}]
    pattern16_bis2 = [{'LOWER': "srtas"}]
    pattern16_bis3 = [{'LOWER': "srtas."}]
    pattern17 = [{'LOWER': 'ud.'}]
    pattern17_bis1 = [{'LOWER': 'uds.'}]
    pattern17_bis2 = [{'LOWER': 'ud'}]
    pattern17_bis3 = [{'LOWER': 'uds'}]
    matcher = Matcher(doc.vocab)
    matcher.add("format_pattern1", None, pattern1)
    matcher.add("format_pattern1_bis1", None, pattern1_bis1)
    matcher.add("format_pattern1_bis2", None, pattern1_bis2)
    matcher.add("format_pattern1_bis3", None, pattern1_bis3)
    matcher.add("format_pattern2", None, pattern2)
    matcher.add("format_pattern3", None, pattern3)
    matcher.add("format_pattern4", None, pattern4)
    matcher.add("format_pattern5", None, pattern5)
    matcher.add("format_pattern6", None, pattern6)
    matcher.add("format_pattern6_bis1", None, pattern6_bis1)
    matcher.add("format_pattern6_bis2", None, pattern6_bis2)
    matcher.add("format_pattern6_bis3", None, pattern6_bis3)
    matcher.add("format_pattern7", None, pattern7)
    matcher.add("format_pattern8", None, pattern8)
    matcher.add("format_pattern9", None, pattern9)
    matcher.add("format_pattern10", None, pattern10)
    matcher.add("format_pattern11", None, pattern11)
    matcher.add("format_pattern12", None, pattern12)
    matcher.add("format_pattern13", None, pattern13)
    matcher.add("format_pattern13_bis1", None, pattern13_bis1)
    matcher.add("format_pattern13_bis2", None, pattern13_bis2)
    matcher.add("format_pattern13_bis3", None, pattern13_bis3)
    matcher.add("format_pattern14", None, pattern14)
    matcher.add("format_pattern14_bis1", None, pattern14_bis1)
    matcher.add("format_pattern15", None, pattern15)
    matcher.add("format_pattern15_bis1", None, pattern15_bis1)
    matcher.add("format_pattern16", None, pattern16)
    matcher.add("format_pattern16_bis1", None, pattern16_bis1)
    matcher.add("format_pattern16_bis2", None, pattern16_bis2)
    matcher.add("format_pattern16_bis3", None, pattern16_bis3)
    matcher.add("format_pattern17", None, pattern17)
    matcher.add("format_pattern17_bis1", None, pattern17_bis1)
    matcher.add("format_pattern17_bis2", None, pattern17_bis2)
    matcher.add("format_pattern17_bis3", None, pattern17_bis3)
    matches = matcher(doc)
    start = 0
    spans = []
    for match_id, start_match, end_match in matches:
        spans.append(doc[start:start_match].text)
        if(doc[start_match].text in ["Sr.","sr.","Sr","sr","SR","SR."]):
            spans.append("Señor")
            start = end_match
        elif(doc[start_match].text in ["Srs.","srs.","Srs","srs","SRS","SRS."]):
            spans.append("Señores")
            start = end_match
        elif(doc[start_match].text=="%"):
            spans.append("por ciento")
            start = end_match
        elif(doc[start_match].text=="`"):
            spans.append("'")
            start = end_match
        elif(doc[start_match].text=="&"):
            spans.append("y")
            start = end_match
        elif(doc[start_match].text=="="):
            spans.append("igual")
            start = end_match
        elif(doc[start_match].text in ["Sra","sra","SRA","Sra.","sra.","SRA."]):
            spans.append("Señora")
            start = end_match
        elif(doc[start_match].text in ["Sras","sras","SRAS","Sras.","sras.","SRAS."]):
            spans.append("Señoras")
            start = end_match
        elif(doc[start_match].text in ["Srta","srta","SRTA","Srta.","srta.","SRTA."]):
            spans.append("Señorita")
            start = end_match
        elif(doc[start_match].text in ["Srtas","srtas","SRTAS","Srtas.","srtas.","SRTAS."]):
            spans.append("Señoritas")
            start = end_match
        elif(doc[start_match].text in ["VD","Vd","VD.","Vd.","vd","vd."]):
            spans.append("usted")
            start = end_match
        elif(doc[start_match].text in ["VDS","Vds","VDS.","Vds.","vds","vds."]):
            spans.append("ustedes")
            start = end_match
        elif(doc[start_match].text in ["UD","Ud","UD.","Ud.","ud","ud."]):
            spans.append("usted")
            start = end_match
        elif(doc[start_match].text in ["UDS","Uds","UDS.","Uds.","uds","uds."]):
            spans.append("ustedes")
            start = end_match
        elif(doc[start_match].text in ["dr.","dr","Dr.","Dr","DR.","DR"]):
            spans.append("doctor")
            start = end_match
        elif(doc[start_match].text in ["dra.","dra","Dra.","Dra","DRA.","DRA"]):
            spans.append("doctora")
            start = end_match
        elif(doc[start_match].text=="+"):
            spans.append("más")
        elif(doc[start_match].text=="h"):
            spans.append("hora")
            start = end_match
        elif(doc[start_match].text=="e"):
            spans.append("euros")
            start = end_match
        elif(doc[start_match].text=="m"):
            spans.append("metros")
            start = end_match
        elif(doc[start_match].text.isspace()):
            start = end_match
    if(start<len(doc)):
        spans.append(doc[start:].text)
    output = " ".join(spans)
    return(nlp.make_doc(output))

def good_caste(doc):
    #accents à conserver
    accents = ["é", "è", "ê", "ë", "à", "â", "ù", "û", "ü", "î", "ï", "ô", "ö", "ç","á","í","ó","ú","ñ","É","È", "Ê", "Ë", "À", "Â", "Ù", "Û", "Ü", "Î", "Ï", "Ô", "Ö", "Ç","Á","Í","Ó","Ú","Ñ"]
#il manque - et ' qui sont des caractères importants 
#"'", "’", 
    puncts = [',', '.', '"', ':', ')', '(', '!', '?', '|', ';', 'σ', '$', '&', '/', '[', ']', '>', '%', '=', '#', '*', '+', '\\', '•',  '~', '@', '£', 
 '·', '_', '{', '}', '©', '^', '®', '`',  '<', '→', '°', '€', '™', '›',  '♥', '←', '×', '§', '″', 'Â', '█', '½', '…', 'β', '∅', 'π', '₹', 'θ', '÷',
 '“', '★', '”', '–', '●', '►', '−', '¢', '²', '¬', '░', '¶', '↑', '±', '¿','¡', '▾', '═', '¦', '║', '―', '¥', '▓', '—', '‹', '─', 
 '▒', '：', '¼', '⊕', '▼', '▪', '†', '■', '▀', '¨', '▄', '♫', '☆', '¯', '♦', '¤', '▲', '¸', '¾', 'τ', 'ζ', 'ω', 'Ã', '⋅', '∞', 
 '∙', '）', '↓', '、', '│', '（', '»', '，', '♪', '╩', '╚', '³', '・', '╦', '╣', '╔', '╗', '▬', '❤', 'Ø', '¹', '≤', '‡', '√', "0","1","2","3","4","5","6","7","8","9"]
    output = []
    for sent in doc.sents:
        temp_sent = [] 
        for token in sent:
            modified_token = ""
            #gérer les problèmes avec les "'"’
            if((token.text=="'") and temp_sent):
                temp_sent[-1] += "'"
                continue
            #vérifier si le token est une suite de '-'
            if("".join(set(token.text))=='-' and len(token.text) > 1):
                continue
            #vérifier si un mot contient l'un des éléments de ponctuation interdit
            if(any(elem in token.text for elem in puncts)):
                continue
            if(any(elem in token.text for elem in accents)):
                modified_token = token.text.lower()
            else:
                modified_token = token.text.encode('ascii', 'ignore').decode('ascii').lower()
            if(modified_token != ""):
                #nouveauté sur la v3
                if(temp_sent and token.text.startswith("-")):
                    if(temp_sent and token.text.endswith("-")):
                        modified_token = token.text[:-1]
                    temp_sent[-1] += modified_token
                #nouveauté sur la v3
                elif(temp_sent and token.text.endswith("-")):
                    modified_token = token.text[:-1]
                    temp_sent.append(modified_token)
		#nouveauté sur la v3
                #elif(temp_sent and temp_sent[-1].endswith("-")):
                #    temp_sent[-1] += modified_token
                else:
                    temp_sent.append(modified_token)
        #condition sur les phrases (on exige des phrases de taille au moins 2 (len(temp_sent)>0) et qui ne commence pas par un tiret)
        if(temp_sent):
            if(temp_sent[0][0]!="-"):
                #dans Le Monde il y a certaines erreurs (des mots avec des tirets), on essaie de voir si le mot
                #sans tiret existe, si oui, on ajoute ce mot
                for i, element in enumerate(temp_sent):
                    if("-" in element):
                        #element sans le tiret, on vérifie si il est en tg_sphinx, si oui, on le rajoute
                        if(re.sub('-', '', element) in tg_sphinx and element not in tg_sphinx):
                            temp_sent[i] = re.sub('-', '', element)
                #nouveauté sur la v3
                if(len(temp_sent)>1):
                    temp_sent = " ".join(temp_sent)
                    output.append(temp_sent)
    output = "\n".join(output)
    doc = nlp.make_doc(output)
    for i, token in enumerate(doc):
        if token.text == "\n":
            doc[i+1].sent_start = True
    return(doc)


nlp = spacy.load('es', disable=['parser','tagger'])
nlp.max_length = 10000000
sbd = SentenceSegmenter(nlp.vocab, strategy=split_on_breaks2)
sbd_last = SentenceSegmenter(nlp.vocab, strategy=split_on_breaks)
#traite les URL et les mails
nlp.add_pipe(treat_url_and_email, first=True)
#chiffres romains
nlp.add_pipe(roman_numbers, after="treat_url_and_email")
#nombres ordinaux (1er => premier)
nlp.add_pipe(ordinal_numbers, after="roman_numbers")
#8.1 devient 8 point 1 et 8,1 devient 8 virgule 1
nlp.add_pipe(treat_floats, after="ordinal_numbers")
#36 000 -> 36000
nlp.add_pipe(treat_bad_digits, after="treat_floats")
#traite les numéros de téléphone
nlp.add_pipe(treat_dates, after="treat_bad_digits")
#traite les dates
nlp.add_pipe(treat_phone_numbers, after="treat_dates")
#transforme les chiffres en texte
nlp.add_pipe(digits_to_words, after="treat_phone_numbers")
nlp.add_pipe(filter_punctuation, after="digits_to_words")
nlp.add_pipe(replace_expressions, after="filter_punctuation")
nlp.add_pipe(sbd, after="replace_expressions")

#dans good_caste, concatener les tokens avec des tirets
nlp.add_pipe(good_caste, after="ner")

print(nlp.pipe_names)


def get_sentences(text):
    doc = nlp(text)
    doc = list(doc.sents)   
    return(doc)


import multiprocessing

inputs = range(len(corpus.split("\n"))//1000)
print("nombre de k : ", len(inputs))

try:
    print("good")
    cpus = multiprocessing.cpu_count()-1
except NotImplementedError:
    cpus = 2   # arbitrary default


def processInput(k):
    output = ""
    list_test = []
    temp = corpus.split("\n")[1000*k:1000*(k+1)]
    for doc in nlp.pipe(temp, batch_size=100, n_threads=32):
        output+=doc.text+"\n"
        #supprimer les espaces en trop
        output = re.sub(' +', ' ',output)
    print(k)
    with open("new_vocab-full.txt", "a+", encoding="utf-8") as text_file:
        text_file.write(output)
        text_file.flush()
        text_file.close()


pool = multiprocessing.Pool(processes=cpus)
print(pool.map(processInput, inputs))


