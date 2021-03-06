#!/usr/bin/python3
from cv2 import cv2
import os
import sys
import paddleocr
import zipfile

try:
    os.remove("result.txt")
except(FileNotFoundError):
    pass

def path_parser(path):
    '''
    Take a path, examine if it's valid, and yield the pictures to be processed
    '''
    if path.endswith(".zip") or path.endswith(".rar"):
        try:
            pics = zipfile.ZipFile(path)
        except(zipfile.BadZipFile):
            print("Please upload a valid picture or zip file!")
            sys.exit()
        namelist = pics.namelist()
        print("{} pictures have been detected!".format(len(namelist)))
        namelist.sort()
        for name in namelist:
            yield pics.extract(name)
    else:
        img = cv2.imread(path)
        if img is None:
            print("Please upload a valid picture!")
            sys.exit()
        else:
            yield path

def cropper(img_path,text_area):
    '''
    Crop the given picture according to the given area
    '''
    img = cv2.imread(img_path)
    if text_area == "Default":
        height,length = img.shape[:2]
        cropped = img[int(height*0.8):height,int(length*0.1):int(length*0.9)]
    else:
        cropped = img[text_area[1]:text_area[3],text_area[0]:text_area[2]]
    return cropped

def transcriber(ocr_tool,img):
    '''
    Read the line in the image
    '''
    result = ocr_tool.ocr(img,cls=True)
    text = []
    for line in result:
        print(line[-1][0])
        text.append(line[-1][0])
    return text

def text_area_test(text_area):
    '''
    Confirm the validity of the text area input
    '''
    if text_area == "Default":
        return True
    try:
        coordinates = [int(i) for i in text_area.split(',')]
        if coordinates[3]>coordinates[1] and coordinates[0]>coordinates[1]:
            return True
    except:
        return False

# Take arguments from the script server
filepath,mode,text_area = sys.argv[1:4]

if not text_area_test(text_area):
    print('''Please check text area parameter. (It has to be "Default" or four integers separated by commas.)''')
    sys.exit()

# Create a text file to write if "Save the result as a .txt file" box is checked 
if "saved" in sys.argv:
    ocr_result = open("result.txt","a+",encoding="utf-8")

print("Initializing the OCR tool...")
ocr_tool = paddleocr.PaddleOCR(use_gpu=False,use_angle_cls=True,use_space_char=True)
print("Getting to work...")
print("=================================================================")
filelist = []
for pic in path_parser(filepath):
    filelist.append(pic)
    if mode == "Full Scale":
        text = transcriber(ocr_tool,pic)
    else:
        cropped = cropper(pic,text_area)
        text = transcriber(ocr_tool,cropped)
    text.append("\n")
    try:
        ocr_result.writelines(text)
    except(NameError):
        pass

try:
    ocr_result.close()
except(NameError):
    pass

# Delete the pictures that have been uploaded or unzipped
for i in filelist:
    os.remove(i)

print("=================================================================")
print("Work complete!")