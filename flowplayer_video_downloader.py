import urllib
import argparse
import logging
import os
import glob
import shutil

def parse_args():
    parser = argparse.ArgumentParser(description="BitTiger Archive Course Downloader")
    # eg. https://cdn-v2.tianmaying.com/272367/266942/720p/1163.ts
    # --segment-path = https://cdn-v2.tianmaying.com/272367/266942/720p/
    parser.add_argument('--segment-path', help='Video Segment URL Path', required=True, type=str)
    # --segment-name = 1164.ts  #.ts  -- I will replace '#' into an index
    parser.add_argument('--segment-name', help='Video Segment Name', required=True, type=str)
    # --target-dir
    parser.add_argument('--target-dir', help='Segment save directory', required=True, type=str)
    # --end-segment = 1163
    parser.add_argument('--end-segment', help='End Index of Segment', required=False, type=int)
    # --start-segment = 0
    parser.add_argument('--start-segment', help='Start Index of Segment', required=False, type=int)
    args = parser.parse_args()
    return args

args = parse_args()
stop_flag = False


def download(url_path):
    try:
        segment = urllib.URLopener()
        segment.retrieve(url_path, os.path.join(args.target_dir, url_path.split('/')[-1]))
        print("Segment: {}  has been downloaded!".format(url_path.split('/')[-1]))
    except IOError as e:
        if "Not Found" in e and 404 in e:
            global stop_flag
            stop_flag = True


def concatenate_segments():
    file_list = glob.glob(os.path.join(args.target_dir , '*.' + args.segment_name.split('.')[-1]))
    file_list.sort()
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


def convert_to_mp4():
    # ref : https://gist.github.com/maxwellito/90a0f1c94c3f6e63e52a
    # ffmpeg -i all.ts -bsf:a aac_adtstoasc -vcodec copy output.mp4
    pass


def main():
    # print("Arguments: {}".format(args.segment_name))
    max_index = 65535 if args.end_segment is None else args.end_segment + 1
    start_index = 0 if args.start_segment is None else args.start_segment
    print("===================Parameters=========================")
    print("Segments URL: {}".format(args.segment_path))
    print("Segments Index: start with {}, end with {}".format(start_index, max_index))
    print("Segment file Name with Mask: {}".format(args.segment_name))
    print("Downloaded segments saved in {}".format(args.target_dir))
    print("=======================================================")

    if not os.path.exists(args.target_dir):
        os.mkdir(args.target_dir)

    for i in xrange(start_index, max_index):
        if stop_flag:
            print("Downloading ending with index of {}".format(str(i-1)))
            break
        url_path = os.path.join(args.segment_path, args.segment_name.replace('#', '{0:04d}'.format(i)))
        print(url_path)
        download(url_path)

    print("Video Segments download finished!")

    concatenate_segments()

if __name__ == "__main__":
    import time
    tic = time.time()
    main()
    toc = time.time() - tic
    print("Download this video take {} seconds".format(int(toc)))