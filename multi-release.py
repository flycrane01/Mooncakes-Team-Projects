#!/usr/bin/python3
import os
import sys
import pysubs2
import re

# example:
# root@ValarDohaeris:~# multi-release.py somesub.srt CN EN CN+EN EN+Names

for i in os.listdir():                                                                         # clean up the existing .srt files in the working directory
    if '.srt' in i:
        os.remove(i)

filepath = sys.argv[1]

try:                                                                                           # load the subtitle file with pysubs2
    sub = pysubs2.load(filepath,encoding='utf-8')
except(UnicodeDecodeError,pysubs2.exceptions.FormatAutodetectionError):
    print('What you uploaded is not a subtitle file...')
    sys.exit()

filename = os.path.splitext(os.path.basename(filepath))[0]                                     # get the filename
version_count = 0                                                                              # count the outputs
ignored = ['Translator','Proofreader','Timing',"Qin's Moon",'Note']                            # mark the lines that should be left unprocessed

if 'CN' in sys.argv:                                                                           # create empty files according to the arguments
    CN_sub = open(filename+'_cn.srt','a+',encoding='utf-8')
    version_count += 1
if 'CN+EN' in sys.argv:
    CNEN_sub = open(filename+'_cn+en.srt','a+',encoding='utf-8')
    version_count += 1
if 'EN+Names' in sys.argv:
    ENWithNames_sub = open(filename+'_en+names.srt','a+',encoding='utf-8')
    version_count += 1
if 'EN' in sys.argv:
    EN_sub = open(filename+'_en.srt','a+',encoding='utf-8')
    version_count += 1

def writer(sub,number,start,end,content):
    '''
    Writes an event in the target subtitle file every time it's called
    '''
    sub.write(str(number)+'\n')
    sub.write(start+' --> '+end+'\n')
    for i in content:
        sub.write(i+'\n')
    sub.write('\n')

def truncater(string):
    '''
    Removes names from the source file
    '''
    pattern = re.compile('(.*: )')
    for i in ignored:                                                                          # ignore some of the lines
        if i in string:
            return string
    else:
        new = re.sub(pattern,'',string)
        return new

for i in range(len(sub)):                                                                      # iterate from the beginning of every event 
    CN_lines = []
    ENWithNames_lines = []
    start = pysubs2.time.ms_to_str(sub[i].start,fractions=True)
    end = pysubs2.time.ms_to_str(sub[i].end,fractions=True)
    dialogues = sub[i].text.split('\\N')
    for dialogue in dialogues:
        for character in dialogue:
            if '\u4e00' <= character <='\u9fff':                                               # if a sentence contains a Chinese character, then it's a Chinese line
                CN_lines.append(dialogue)
                break
        else:
            ENWithNames_lines.append(dialogue)                                                 # if a sentence doesn't contain any Chinese characters, it's an English line with names
    EN_lines = [truncater(i) for i in ENWithNames_lines]                                       # remove the names from the English lines, and you'll have the English lines
    try:                                                                                       # write the events with the separated lines
        writer(CN_sub,str(i+1),start,end,CN_lines)
    except(NameError):
        pass
    try:
        writer(CNEN_sub,str(i+1),start,end,CN_lines+EN_lines)
    except(NameError):
        pass
    try:
        writer(ENWithNames_sub,str(i+1),start,end,ENWithNames_lines)
    except(NameError):
        pass
    try:
        writer(EN_sub,str(i+1),start,end,EN_lines)
    except(NameError):
        pass

try:                                                                                           # close the files
    CN_sub.close()
except(NameError):
    pass
try:
    CNEN_sub.close()
except(NameError):
    pass
try:
    ENWithNames_sub.close()
except(NameError):
    pass
try:
    EN_sub.close()
except(NameError):
    pass

print('%s has been processed with %s output(s).' % (filename,version_count))
