import os, subprocess, sys
if __name__ == '__main__':
    python = os.environ['RESEARCH_INFERENCE_PYTHON']
    raise SystemExit(subprocess.call([python, '/materials/code/run_frames.py', *sys.argv[1:]]))
