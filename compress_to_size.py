import os
import sys
import inspect
import pkg_resources

#make sure additional packages are installed
required = {'opencv-python', 'ffmpeg'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed
if missing:
    python = sys.executable
    subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)

import cv2

def getextensionstartindex(filename):
    i = len(filename) - 1
    while i >= 0:
        if filename[i] == '.':
            return i
        i -= 1
    raise Exception("File name must contain a file extension.")

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = input("Enter input file: ")
    input_file = input_file.replace("\"", "\\\"")

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = input("Enter output file (defaults to adding \"_compressed\" to end of input file name): ")

    if output_file == "" or output_file == "std":
        extension_start_index = getextensionstartindex(input_file)
        output_file = input_file[:extension_start_index] + "_compressed." + input_file[extension_start_index + 1:]
        print(f"Output file is {output_file}")
    output_file = output_file.replace("\"", "\\\"")

    
    print(output_file[getextensionstartindex(output_file) + 1:])
    if output_file[getextensionstartindex(output_file) + 1:] == "webm":
        video_encoder = "libvpx-vp9"
        audio_encoder = "libopus"
        file_removal = " ; rm ffmpeg2pass-0.log"
    else:
        video_encoder = "libx264"
        audio_encoder = "aac"
        file_removal = " ; rm ffmpeg2pass-0.log ; rm ffmpeg2pass-0.log.mbtree"

    if len(sys.argv) > 3:
        target_size = float(sys.argv[3])
    else:
        target_size = float(input("Enter target filesize in MB: "))

    if len(sys.argv) > 4:
        target_audio_bitrate = sys.argv[4]
    else:
        target_audio_bitrate = input("Enter audio bitrate in kBit/s (defaults to 128kBit/s): ")

    if target_audio_bitrate == "" or target_audio_bitrate == "std":
        target_audio_bitrate = 128
    else:
        target_audio_bitrate = int(target_audio_bitrate)

    video = cv2.VideoCapture(input_file)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS)
    #fields = json.loads(subprocess.check_output(f'ffprobe -v quiet -show_streams -select_streams v:0 -of json "{input_file}"', shell=True).decode())['streams'][0]
    #duration = float(fields['tags']['DURATION'])
    if duration == 0:
        print("Video duration must not be 0.")
        return

    target_video_bitrate = int(target_size * 8000 / duration - target_audio_bitrate)
    if target_video_bitrate <= 0:
        print(f"Target video bitrate is too small ({target_video_bitrate}). Either decrease audio bitrate or increase target file size.")
        return

    command = f"ffmpeg -y -i \"{input_file}\" -c:v {video_encoder} -b:v {target_video_bitrate}k -pass 1 -an -f null /dev/null && ffmpeg -i \"{input_file}\" -c:v {video_encoder} -b:v {target_video_bitrate}k -pass 2 -c:a {audio_encoder} -b:a {target_audio_bitrate}k \"{output_file}\" && echo \"Finished succesfully!\" || rm \"{output_file}\" ; rm ffmpeg2pass-0.log ; rm ffmpeg2pass-0.log.mbtree"
    os.system(command)

main()
