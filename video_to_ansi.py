import cv2
import os
import sys
import time
import subprocess
import argparse
import shutil

# ---------- ANSI HELPERS ----------
def fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def bg(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"

# ---------- FRAME → ANSI HALF-BLOCK ----------
def frame_to_ansi(frame, term_width, term_height):
    h, w, _ = frame.shape
    max_width = term_width
    max_height = term_height * 2  # half-block doubles vertical resolution

    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h)

    new_w = max(1, int(w * scale))
    new_h = max(2, int(h * scale))

    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    out = ""
    for y in range(0, new_h - 1, 2):
        top = frame[y]
        bot = frame[y + 1]
        for x in range(new_w):
            out += fg(*top[x]) + bg(*bot[x]) + "▀"
        out += "\033[0m\n"
    return out

# ---------- AUDIO ----------
def play_audio(video):
    subprocess.Popen([
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", video
    ])

# ---------- MAIN ----------
def main():
    parser = argparse.ArgumentParser(description="CLI ANSI Video Player – Terminal Size, TRUE 1x speed")
    parser.add_argument("video", help="Local video file path")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print("❌ Video file not found")
        sys.exit(1)

    term_size = shutil.get_terminal_size((80, 24))
    term_width, term_height = term_size.columns, term_size.lines

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
    frame_delay = 1 / fps

    if not args.no_audio:
        play_audio(args.video)

    os.system("clear")
    print("\033[?25l", end="")  # hide cursor

    # Track exact video time
    video_start_time = time.time()
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ansi = frame_to_ansi(frame, term_width, term_height)
        print("\033[H" + ansi, end="")

        # Calculate when the next frame should be displayed
        frame_count += 1
        target_time = video_start_time + frame_count * frame_delay
        sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    print("\033[0m\033[?25h")  # reset + show cursor

if __name__ == "__main__":
    main()
