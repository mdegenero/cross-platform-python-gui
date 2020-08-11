#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Virtual_Ensemble.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oTiETsnT1gd7Ta2nSIguzsQrhQmhF0Ia

# VIRTUAL MUSIC ENSEMBLE TECHNOLOGIES, LLC.

## -- Desktop Application Prototype --

IMPORTANT: All code must be kept strictly confidential and not shared with anyone outside the company.

#Saving Instructions:
+Do not edit the master copy: "Virtual_Ensemble.ipynb".

+Instead make a copy to your folder within the engineering folder.

+Name your copy: "VMET_yourinitials_month_day.ipynb"

--->for example: "VMET_BE_06_05.ipynb".

+Create a new copy to work on at the start of each editing session.

+We'll add to the master copy only when code sections are working well.

# Links:
https://github.com/MalFan/tile-videos/blob/master/tile_videos.py

https://github.com/xaliceli/video-mosaic

https://opencv.org/
"""

#General Imports
import numpy as np

#from google.colab import output
import cv2
import math
import random
import sys
from scipy import ndimage
import os
import time
import subprocess
#from google.colab import files
#from google.colab.patches import cv2_imshow
import moviepy.editor as mp
import shutil
import skimage.transform as st
from functools import partial
#import sox

#Frame Counting Import
#!pip install --upgrade imutils
import imutils
from imutils import video
from imutils.video import count_frames

#Audio Mixing Import
#!pip install ffmpeg #NOTE ! ONLY FOR COLAB
#!apt-get install sox libsox-fmt-mp3
global PROG
PROG = 0
global PERCENT
PERCENT = 0
global ACTION
ACTION = "Resizing videos..."


class Processor:

    def __init__(self, files, img_count, **kwargs):
        super(Processor, self).__init__(**kwargs)
        self.FILES = files
        self.IMG_COUNT = img_count
        self.cancelled = False

    """ ## 1.) Delete Files from Previous Render"""
    def clear_extra_files(self):
        print("CLEARING EXTRA FILES")
        if (os.path.isdir("./tiles/")):
            shutil.rmtree('./tiles')
        if (os.path.isfile("audio_temp.mp3")):
            os.remove("audio_temp.mp3")
        if (os.path.isfile("video_temp.mp4")):
            os.remove("video_temp.mp4")

    """## 2.) Create Rescaled Videos in New Folder"""


    def tile_dim(self, num_vid, dimensions):
        """Calculates the dimensions of one tile based on number of videos and final video dimensions"""

        ##if (num_vid == 2):
            ##height = np.floor(dimensions[1])
            ##width = np.floor(dimensions[0] / 2)

        #Assume perfect squares as grids, could become more advanced
        ##else:
        size = np.ceil(np.sqrt(num_vid))
            #height = np.floor(dimensions[1] / size)
            #width = np.floor(dimensions[0] / size)
        height = dimensions[1]/size
        width = dimensions[0]/size
        return height, width

    def resize_vid(self, vid, folder, h, w, vid_id):
        """Resizes a single video and outputs to new folder"""

        print("path: ", vid)
        clip = mp.VideoFileClip(vid)
        resized = clip.resize(height = h) # Width is computed so that the width/height ratio is conserved.)

        #Write new resized video
        resize_path = folder + str(vid_id) + '.mp4' #path and name for resized vid, ex: "./tile/3.mp4"
        resized.write_videofile(resize_path) # Write new video into tiles folder

    def resize_all(self, vid_path='./recordings/test'):
        """Resizes all videos in folder to new folder"""

        print('----------------------------')
        print('Resizing videos...')
        print('----------------------------')

        # Create new folder for resized videos
        folder = './tiles/'
        if not os.path.isdir(folder):
            os.mkdir(folder)
            print('mkdir')

        # Find number of videos
        num_vid = 0
        #for filename in os.listdir(vid_path):
            #num_vid = num_vid + 1
        for filename in self.FILES:
            num_vid = num_vid + 1
        print('Num: ', num_vid)

        # Find tile dimensions
        dimensions = np.array([1280, 720])
        height, width = self.tile_dim(num_vid, dimensions)
        height = int(height)
        width = int(width)
        print('Dim: ', height, width)

        # Resize videos and save into folder
        vid_id = 1
        #for filename in os.listdir(vid_path):
        for filename in self.FILES:
            self.resize_vid(filename, folder, height, width, vid_id)
            vid_id = vid_id + 1

        return num_vid, height, width

    """## 3.) Create Tiled Video"""

    def get_blank(self, width, height, rgb_color = (0,0,0)):
        """Create placeholder blank frame (numpy array) filled with black color"""

        # Create black blank image
        blank = np.zeros((height, width, 3), np.uint8)

        # Since OpenCV uses BGR, convert the color first
        color = tuple(reversed(rgb_color))

        # Fill image with color
        blank[:] = color

        return blank

    def tile_frame(self, img, num_vid, tile_height, tile_width, num_frames, total):
        """Creates one tiled video frame from input frames"""
        #if (num_vid ==2): # Special case of 2 videos
            #frame = np.concatenate((img[0], img[1]), axis=1

        #else: # All other cases

        # Determine parameters of tile array
        size = np.ceil(np.sqrt(num_vid)) #num of images for each row and col
        size = size.astype(int)
        num_full = np.floor(num_vid / size) #num of full rows
        num_full = num_full.astype(int)
        last_imgs = num_vid % size #num of images in bottom partial row
        if(last_imgs == 0 and num_full == size):
            blanks = 0
        else:
            blanks = size - last_imgs #num of blank tiles in bottom partial row
        tile_size = np.shape(img[0]) #dim of 1 tile
        row_size = np.array((tile_size[0], tile_size[1]*size, tile_size[2])) #dim of row of tiles
        row_size = row_size.astype(int)

        # First fill all the full rows
        im_num = 0 #Keep track of which image index to add
        full_rows = np.empty(row_size)
        for row in range(num_full):
            temp = img[im_num]
            im_num = im_num + 1
            for col in range(size-1):
                temp = np.concatenate((temp, img[im_num]), axis=1)
                im_num = im_num + 1
            full_rows = np.concatenate((full_rows, temp), axis=0)

        if(blanks != 0):
            # Then add images to last partial row
            last_row = np.empty(tile_size)
            for im in range(last_imgs):
                last_row = np.concatenate((last_row, img[im_num]), axis=1)
                im_num = im_num + 1

            # Then add blanks to partial row
            blank_tile = self.get_blank(tile_width, tile_height)
            for blank in range(blanks):
                last_row = np.concatenate((last_row, blank_tile), axis=1)
            # Trim last row, first column
            last_row = last_row[:, tile_width:, :]
            # Finally concatenate last row to full rows
            frame = np.concatenate((full_rows, last_row), axis=0)

            #ADDED: add another row of blanks if needed - same process
            if(size - num_full > 1):
                blank_row = np.empty(tile_size)
                blank_tile = self.get_blank(tile_width, tile_height)
                for blank in range(size):
                    blank_row = np.concatenate((blank_row, blank_tile), axis=1)
                blank_row = blank_row[:, tile_width:, :]
                frame = np.concatenate((frame, blank_row), axis=0)
        else:
            frame = full_rows
        # Trim entire first row
        frame = frame[tile_height:, :, :]
        frame = st.resize(frame, (720, 1280))
        self.prog(total)
        return frame

    def tile_video(self, num_vid, height, width, output_file, num_frames, total):
        global ACTION
        ACTION = "Tiling video..."
        """Create tiled video output"""
        print('----------------------------')
        print('Tiling video...')
        print('----------------------------')

        #Set video folder location
        vid_path = './tiles/'

        #Count number of frames in first video (assumes each video has same number of frames)
        #first = os.listdir(vid_path)[0]
        #first_path = self.FILES[0]
        #first_path = vid_path + first
        #num_frames = count_frames(first_path, False)
        print(num_frames)

        #Initialize final video storage
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        #PREVIOUSLY ./recordings/video_temp.mp4
        video=cv2.VideoWriter('./video_temp.mp4', fourcc, 30, (1280,720), True)

        #Tile video frame by frame
        for fm in range(num_frames): #loop through each frame (set range to num_frames to run full length)
            images = np.empty((num_vid, height, width, 3)) #initialize array to hold a single image from each video
            idx = 0
            for filename in os.listdir(vid_path): #loop through each video
                vd = vid_path + filename #concatenate folder and file names
                vidcap = cv2.VideoCapture(vd) #create video object
                vidcap.set(1, fm) #set video frame to frame number
                _, image = vidcap.read() #get frame
                images[idx, :, :, :] = image
                idx += 1
            frame = self.tile_frame(images, num_vid, height, width, num_frames, total)
            frame = np.uint8(frame)
            video.write(frame)
            self.prog(total)
        video.release()

    """## 4.) Mix Audio Channels"""

    def mix_audio(self, audio_file, total):
        global ACTION
        ACTION = "Mixing audio..."
        print('----------------------------')
        print('Mixing audio...')
        print('----------------------------')
        delayed_audios = []
        audios = []
        offset = 0
        #audio_file = vid_path + audio_file

        flist = []
        #for filename in os.listdir(vid_path):
        for filename in self.FILES:
            if (filename == '.ipynb_checkpoints'):
                #do nothing; to avoid issues with colab
                z = 0
            elif (filename not in flist):
                #video_file = os.path.join(vid_path, filename)
                video_file = filename
                #print(filename)
                mp4_file = video_file
                file_name = video_file.split('.')[0]
                mp3_file = file_name + '.mp3'
                #print(mp3_file)

                # Extract audio (check github if wanting to trim videos)
                subprocess.call('ffmpeg -i %s -b:a 192K -vn %s' % (mp4_file, mp3_file), shell=True)
                audios.append(mp3_file)
            flist.append(filename)

        #Mix all mp3 files into one audio_file
        subprocess.call('sox -m %s %s' % (' '.join(audios), audio_file), shell=True)

        #Remove separate mp3 files
        for audio in audios:
            subprocess.call('rm %s' % (audio), shell=True)

        self.prog(total)

    """## 5.) Final Output Video"""

    def combine(self, video_file, audio_file, output_file, total):
        global ACTION
        ACTION = "Combining video and audio..."
        print('----------------------------')
        print('Combining video and audio...')
        print('----------------------------')
        # audio_path = './recordings/test/' + audio_file
        # video_path = './recordings/' + video_file
        output_path = './' + output_file
        print(video_file)
        print(audio_file)
        print(output_file)
        subprocess.call("ffmpeg -i %s -i %s -shortest %s" % (video_file, audio_file, output_path), shell=True)
        self.prog(total)

    def remove_temp_files(self, video_file, audio_file):
        global ACTION
        ACTION = "Removing temporary files..."
        print('----------------------------')
        print('Removing temporary files...')
        print('----------------------------')
        # audio_path = './recordings/test/' + audio_file
        # video_path = './recordings/' + video_file
        subprocess.call('rm %s' % (video_file), shell=True)
        subprocess.call('rm %s' % (audio_file), shell=True)
        shutil.rmtree('./tiles/')
        # for x in range(self.IMG_COUNT):
        #     name = 'test' + str(x) + '.png'
        #     os.remove(name)

    # Function that calculates progress
    def prog(self, total):
        global PROG
        global PERCENT
        PROG+=1
        PERCENT = int((PROG/total)*100)
        # print(PROG)
        # print(total)
        # print(PERCENT)

    def cancel(self):
        self.cancelled = True


    #MAIN THAT CALLS ALL FUNCTIONS
    def run_app(self, filename):
        print('FINAL FILENAME:', filename)
        if os.path.isfile(filename):
            filename = filename + '1'
        #self.unzip()
        print(self.FILES)

        #FOLDER = './Desktop/VMET/test/'
        DIM = (1920,1080)

        # Find number of videos
        num_vid = 0
        for fname in self.FILES:
            num_vid+=1

        # Find number of frames in videos
        first = self.FILES[0]

        if self.cancelled:
            return
        num_frames = count_frames(first, False)
        # Calculate total progress bar size
        total = num_frames + num_vid + num_frames

        if self.cancelled:
            return
        self.clear_extra_files()
        if self.cancelled:
            return
        num_vid, height, width = self.resize_all()
        if self.cancelled:
            return
        self.tile_video(num_vid, height, width, 'video_temp.mp4', num_frames, total)
        if self.cancelled:
            return
        self.mix_audio('audio_temp.mp3', total)
        if self.cancelled:
            return
        self.combine('video_temp.mp4', 'audio_temp.mp3', filename, total) #FINAL WRITE
        if self.cancelled:
            return
        self.remove_temp_files('video_temp.mp4', 'audio_temp.mp3')
