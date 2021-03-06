#!/usr/bin/python3
from cv2 import cv2
import os
import sys
import paddleocr
import pysubs2
from tqdm import tqdm
from difflib import SequenceMatcher
import random

print("Initializing the OCR tools...")
# scanning is faster with the mini model
ocr_tool_det = paddleocr.PaddleOCR(
                            use_gpu=False,
                            use_space_char=True,
                            det_model_dir=r"/root/.paddleocr/2.0-mini/det",
                            rec_model_dir=r"/root/.paddleocr/2.0-mini/rec")
# recognization uses the full model
ocr_tool_rec = paddleocr.PaddleOCR(use_gpu=False,use_space_char=True)
print("Getting to work...")
print("=================================================================")

def transcriber(img, middle_line):
    '''
    Takes a image and returns the text in the img
    '''
    try:
        result = ocr_tool_rec.ocr(img)
    except (IndexError):
        result = ocr_tool_det.ocr(img)
    text = []
    for line in result:
        coords, content = line
        if abs((coords[0][0]+coords[2][0])/2 - middle_line) < 150:            # hardsubs don't really drift too far away from the center of the picture
            text.append(content[0])
    return text

def is_hardsubbed_img(img, middle_line):
    '''
    Takes a image and returns if it contains any hardsub
    '''
    result = ocr_tool_det.ocr(img,rec=False)
    if len(result) > 0:
        for line in result:
            if abs((line[0][0]+line[2][0])/2 - middle_line) < 150:            # hardsubs don't really drift too far away from the center of the picture
                return True

def writer(sub,number,start,end,content):
    '''
    Writes an event in the target subtitle file every time it's called
    '''
    sub.write(str(number)+'\n')
    sub.write(start+' --> '+end+'\n')
    for i in content:
        sub.write(i+'\n')
    sub.write('\n')

def is_same_sentence(str1,str2):
    '''
    Takes two strings and returns if they're the same sentence
    '''
    str1 = ''.join(str1)
    str2 = ''.join(str2)
    if SequenceMatcher(None,str1,str2).ratio() >= 0.5:
        return True

def string_to_frame(string):
    '''
    Transforms the Start/End inputs into frame numbers
    '''
    try:
        frame = int(string)
    except(ValueError):
        timing = string.split(":")
        try:
            for i in timing:
                j = int(i)
        except(ValueError):
            print("Please confirm your Start/End inputs!")
            sys.exit()
        if len(timing) == 1 or len(timing) >= 4:
            print("Please confirm your Start/End inputs!")
            sys.exit()
        elif len(timing) == 2:
            frame = int(timing[0]) * 60 * 30 + int(timing[1]) * 30
        else:
            frame = int(timing[0]) * 60 * 60 * 30 + int(timing[1]) * 60 * 30 + int(timing[2]) * 30
        return frame

# Parse arguments from the script server
video, start, end = sys.argv[1:]

# Get basic information of the video
video_cap = cv2.VideoCapture(video)
frames_count = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = video_cap.get(cv2.CAP_PROP_FPS)
middle_line = 0.4*(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))

# Process the Start/End inputs
if start == "Default":
    start = 0
else:
    start = string_to_frame(start)

if end == "Default":
    end = frames_count
else:
    end = string_to_frame(end)

# Create a temporary folder to contain the frames of the video
alpha_num = 'abcdefghijklmnopqrstuvwxyz1234567890'

while True:
    folder = "/scripts-files/hardsub-ripping-video/cropped/" + "".join(random.sample(alpha_num, 10))
    try:
        os.mkdir(folder)
        break
    except(FileExistsError):
        continue

# Prepare the variables that will be used
subbed_img_index = []
starts = []
ends = []
filename = os.path.splitext(os.path.basename(video))[0]
sub = open(filename+".srt","a+",encoding='utf-8')
subbed_img_index = []

print("(1/4) Extracting pictures to a temporary folder...")

for i in tqdm(range(end), unit="frames"):
    ret, frame = video_cap.read()
    if i >= start:
        height, width = frame.shape[:2]
        cropped = frame[int(height*0.8):height,int(width*0.1):int(width*0.9)]
        writing = cv2.imwrite(folder+str(i)+".jpg",cropped)

print("(2/4) Scanning for the hardsubbed pictures...")

for i in tqdm(range(start, end),unit="pics"):
    img = folder+str(i)+'.jpg'
    if is_hardsubbed_img(img, middle_line):
        subbed_img_index.append(i)

print("(3/4) Retrieving timings...")

for i in subbed_img_index:
    # If a frame is hardsubbed, the frame before it ISN'T hardsubbed, and the frame after it IS hardsubbed,
    # then this frame marks the beginning of a dialogue.
    # If a frame is hardsubbed, the frame before it IS hardsubbed, and the frame after it ISN't hardsubbed,
    # then this frame marks the end of a dialogue.
    if i == 0 and i in subbed_img_index:
        starts.append(i)
    elif 1 < i < (end-1):
        if i-1 not in subbed_img_index and i+1 in subbed_img_index:
            starts.append(i)
        if i-1 in subbed_img_index and i+1 not in subbed_img_index:
            ends.append(i)
    elif i == (end-1) and i in subbed_img_index:
        ends.append(i)

for i in tqdm(range(len(starts)),unit="pics"):
    content_start = transcriber(folder + str(starts[i]) + '.jpg', middle_line)
    content_end = transcriber(folder + str(ends[i]) + '.jpg', middle_line)
    if not is_same_sentence(content_start,content_end):
        # If the start and the end of a dialogue isn't the same (usually when the first speaker is interrupted by the second speaker),
        # this dialogue has to be subdivided.
        for j in range(ends[i],starts[i],-1):
            boundary = transcriber(folder + str(j) + '.jpg', middle_line)
            if not is_same_sentence(boundary,content_end):
                starts.append(j+1)
                ends.append(j)
                if is_same_sentence(boundary,content_start):
                    break
                else:
                    content_end = boundary

print("(4/4) Writing the subtitle file...")
for i in tqdm(range(len(ends)),unit="events"):
    start = pysubs2.time.ms_to_str(pysubs2.time.frames_to_ms(starts[i],fps),fractions=True)
    end = pysubs2.time.ms_to_str(pysubs2.time.frames_to_ms(ends[i]+1,fps),fractions=True)
    content = transcriber(folder + str(int((starts[i]+ends[i]+1)/2)) + '.jpg', middle_line)
    writer(sub,i+1,start,end,content)

sub.close()

print("=================================================================")
print("Work complete!")