#!/usr/bin/env python3
"""
AgileX Scout Mini Simulation — High-Definition Automated Screen Recorder
Captures 1080p full desktop demonstration to MP4 video.
"""

import os
import sys
import time
import signal
import argparse
import numpy as np
import cv2
import mss

running = True

def sig_handler(sig, frame):
    global running
    print("\n🛑 Stop signal received. Finalizing video recording...")
    running = False

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

def main():
    parser = argparse.ArgumentParser(description="Desktop Screen Recorder for ROS 2 AgileX Demo")
    parser.add_argument("--output", "-o", default="recordings/agilex_civil_patrol_demo.mp4", help="Output MP4 file path")
    parser.add_argument("--duration", "-d", type=float, default=0, help="Duration in seconds (0 = until stopped)")
    parser.add_argument("--fps", type=float, default=24.0, help="Frames per second")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    with mss.MSS() as sct:
        # Capture primary monitor (full 1920x1080)
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        width = monitor["width"]
        height = monitor["height"]

        # H.264 plays everywhere and is far smaller; fall back to MPEG-4 part 2 if unavailable
        out = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*'avc1'), args.fps, (width, height))
        if not out.isOpened():
            out = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*'mp4v'), args.fps, (width, height))

        print("=" * 65)
        print("🎥 AgileX Screen Recorder Started")
        print(f"   Output:   {args.output}")
        print(f"   Geometry: {width}x{height} @ {args.fps:.1f} FPS")
        if args.duration > 0:
            print(f"   Duration: {args.duration:.1f} seconds")
        else:
            print("   Duration: Until stopped (Ctrl+C / SIGTERM)")
        print("=" * 65)

        start_time = time.time()
        frame_interval = 1.0 / args.fps
        frames_recorded = 0

        while running:
            t_start = time.time()
            elapsed = t_start - start_time
            if args.duration > 0 and elapsed >= args.duration:
                print(f"⏱️ Reached duration limit ({args.duration:.1f}s).")
                break

            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            # Keep the video at real-time speed: if capture fell behind, repeat this frame
            due = int((time.time() - start_time) * args.fps) + 1
            for _ in range(max(1, due - frames_recorded)):
                out.write(bgr_frame)
                frames_recorded += 1

            if frames_recorded % int(args.fps * 5) == 0:
                print(f"   ⏺️ Recording... [{elapsed:.1f}s elapsed | {frames_recorded} frames captured]")

            t_elapsed = time.time() - t_start
            t_sleep = frame_interval - t_elapsed
            if t_sleep > 0:
                time.sleep(t_sleep)

        out.release()
        total_time = time.time() - start_time
        print("\n✅ Video recording finalized successfully!")
        print(f"   📁 Saved to: {os.path.abspath(args.output)}")
        print(f"   ⏱️ Total Duration: {total_time:.1f} seconds ({frames_recorded} frames)")

if __name__ == "__main__":
    main()
