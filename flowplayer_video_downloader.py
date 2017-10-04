import urllib
import argparse
import logging
import os
import glob
import shutil
import re
import subprocess


def parse_args():
    parser = argparse.ArgumentParser(description="BitTiger Archive Course Downloader")
    # eg. https://cdn-v2.tianmaying.com/272367/266942/720p/1163.ts
    # eg. https://dq59ioeqhrg9x.cloudfront.net/bitmovin/600178_7c003dcc09cc2810e9ee4faf0662385d/video_0_2400000/dash/init.mp4
    # --segment-path = https://cdn-v2.tianmaying.com/272367/266942/720p/
    parser.add_argument('--segment-path', help='Video Segment URL Path', required=True, type=str)
    parser.add_argument('--audio-segment-path', help='Audio Segment URL Path', required=False, type=str)
    # --segment-name = 1164.ts  #.ts  -- I will replace '#' into an index
    parser.add_argument('--segment-name', help='Video Segment Name', required=True, type=str)
    # --target-dir
    parser.add_argument('--target-dir', help='Segment save directory', required=True, type=str)
    # --end-segment = 1163
    parser.add_argument('--end-segment', help='End Index of Segment', required=False, type=int)
    # --start-segment = 0
    parser.add_argument('--start-segment', help='Start Index of Segment', required=False, type=int)
    # --download-audio
    parser.add_argument('--download-audio', help='Some stream split the audio and video', required=False, type=bool)
    # --output-filename
    parser.add_argument('--output-filename', help='File name for output video', required=False, type=str)
    args = parser.parse_args()
    return args

args = parse_args()
stop_flag = False


def download(url_path, dest_path=None):
    if dest_path is None:
        save_folder = args.target_dir
    else:
        save_folder = dest_path
    try:
        segment = urllib.URLopener()
        segment.retrieve(url_path, os.path.join(save_folder, url_path.split('/')[-1]))
        print("Segment: {}  has been downloaded!".format(url_path.split('/')[-1]))
    except IOError as e:
        if "Not Found" in e and 404 in e:
            global stop_flag
            stop_flag = True

def download_init():
    video_init_file = os.path.join(args.segment_path, 'init.mp4')
    audio_init_file = os.path.join(args.audio_segment_path, 'init.mp4')
    init_file = urllib.URLopener()
    print(video_init_file)
    init_file.retrieve(video_init_file, os.path.join(args.target_dir, 'video', 'init.mp4'))
    print("Segment: {}  has been downloaded!".format(video_init_file.split('/')[-1]))

    init_file = urllib.URLopener()
    print(audio_init_file)
    init_file.retrieve(audio_init_file, os.path.join(args.target_dir, 'audio', 'init.mp4'))
    print("Segment: {}  has been downloaded!".format(audio_init_file.split('/')[-1]))


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [ atoi(c) for c in re.split('(\d+)', text) ] 


def concatenate_segments():
    if args.download_audio is True:
        video_file_list = glob.glob(os.path.join(args.target_dir, 'video', '*.' + args.segment_name.split('.')[-1]))
        audio_file_list = glob.glob(os.path.join(args.target_dir, 'audio', '*.' + args.segment_name.split('.')[-1]))
        video_file_list.sort(key=natural_keys)
        audio_file_list.sort(key=natural_keys)
        audio_file_name = os.path.join('./' , 'audio.' + args.segment_name.split('.')[-1].strip())
        video_file_name = os.path.join('./' , 'video.' + args.segment_name.split('.')[-1].strip())

        audio_f = open(audio_file_name, 'wb')
        print("Merging audio init file {} ".format(os.path.join(args.target_dir, 'audio', 'init.mp4')))
        shutil.copyfileobj(open(os.path.join(args.target_dir, 'audio', 'init.mp4')), audio_f)
        print("All of audio segment will be merged into {}".format(audio_file_name))
        for file in audio_file_list:
            print("Merging {} ...".format(file))
            shutil.copyfileobj(open(file, 'rb'), audio_f)
        audio_f.close()
        print("All of audio segments have been merged into {}".format(audio_file_name))

        video_f = open(video_file_name, 'wb')
        print("Merging video init file {} ".format(os.path.join(args.target_dir, 'video', 'init.mp4')))
        shutil.copyfileobj(open(os.path.join(args.target_dir, 'video', 'init.mp4')), video_f)
        print("All of video segment will be merged into {}".format(video_file_name))
        for file in video_file_list:
            print("Merging {} ...".format(file))
            shutil.copyfileobj(open(file, 'rb'), video_f)
        video_f.close()
        print("All of video segments have been merged into {}".format(video_file_name))
        print("Now you can use below command to convert this merged file to one")
        print("    $ ffmpeg -i [input_video] -i [input_audio] -acodec copy -vcodec copy [output_file_name]")
        print("    $ ffmpeg -i video.m4s -i audio.m4s -acodec copy -vcodec copy output.mp4")
    else:
        file_list = glob.glob(os.path.join(args.target_dir , '*.' + args.segment_name.split('.')[-1]))
        file_list.sort(key=natural_keys)
        target_file_name = os.path.join('./' , 'all.' + args.segment_name.split('.')[-1].strip())
        target_file = open(target_file_name, 'wb')
        print("All of video segment will be merged into {}".format(target_file_name))
        for file in file_list:
            print("Merging {} ...".format(file))
            shutil.copyfileobj(open(file, 'rb'), target_file)
        target_file.close()
        print("All of video segments have been merged into {}".format(target_file_name))
        print("Now you can use below command to convert this merged file to one")
        print("    $ ffmpeg -i [input_file_name] -bsf:a aac_adtstoasc -vcodec copy [output_file_name]")
        print("    $ ffmpeg -i all.ts -bsf:a aac_adtstoasc -vcodec copy output.mp4")


def convert_to_mp4(output_filename):
    # ref : https://gist.github.com/maxwellito/90a0f1c94c3f6e63e52a
    # ffmpeg -i all.ts -bsf:a aac_adtstoasc -vcodec copy output.mp4
    print("Combining and converting to MP4 file...")
    if args.download_audio is True:
        subprocess.call(["ffmpeg", "-i", "video.m4s", "-i", "audio.m4s",
                         "-acodec", "copy", "-vcodec", "copy", output_filename])
    else:
        subprocess.call(["ffmpeg", "-i", "all.ts", "-bsf:a", "aac_adtstoasc", "-vcodec", "copy", output_filename])
    print("MP4 file converted as {}".format(output_filename))


def main():
    # print("Arguments: {}".format(args.segment_name))
    max_index = 65535 if args.end_segment is None else args.end_segment + 1
    start_index = 0 if args.start_segment is None else args.start_segment
    output_filename = "output.mp4" if args.output_filename is None else args.output_filename
    print("===================Parameters=========================")
    print("Segments URL: {}".format(args.segment_path))
    print("Audio Segments URL: {}".format(args.audio_segment_path))
    print("Segments Index: start with {}, end with {}".format(start_index, max_index))
    print("Segment file Name with Mask: {}".format(args.segment_name))
    print("Downloaded segments saved in {}".format(args.target_dir))
    print("Output file name: {}".format(output_filename))
    print("=======================================================")

    if not os.path.exists(args.target_dir):
        os.mkdir(args.target_dir)
        if args.download_audio is True:
            os.mkdir(os.path.join(args.target_dir, 'video'))
            os.mkdir(os.path.join(args.target_dir, 'audio'))

    if args.download_audio is True:
        download_init()

    for i in xrange(start_index, max_index):

        if args.download_audio is True:
            url_path = os.path.join(args.segment_path, args.segment_name.replace('#', str(i)))
            audio_url_path = os.path.join(args.audio_segment_path, args.segment_name.replace('#', str(i)))
            print(url_path)
            download(url_path, os.path.join(args.target_dir, 'video'))
            print(audio_url_path)
            download(audio_url_path, os.path.join(args.target_dir, 'audio'))
        else:
            padding_format = '{0:0' + str(args.segment_name.count('#')) + 'd}'
            url_path = os.path.join(args.segment_path, args.segment_name.replace('#' * args.segment_name.count('#'),
                                                                                 padding_format.format(i)))
            # url_path = os.path.join(args.segment_path, args.segment_name.replace('#', '{0:04d}'.format(i)))
            print(url_path)
            download(url_path)

        if stop_flag:
            print("Downloading ending with index of {}".format(str(i)))
            break

    print("Video Segments download finished!")

    concatenate_segments()

    convert_to_mp4(output_filename)

if __name__ == "__main__":
    import time
    tic = time.time()
    main()
    toc = time.time() - tic
    print("Download this video take {} seconds".format(int(toc)))
