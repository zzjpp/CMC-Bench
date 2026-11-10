"""Run corpus validation and the complete standard-library regression suite."""
import subprocess
import sys
from common import ROOT


def main():
    subprocess.run([sys.executable,str(ROOT/'tools/validate.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)


if __name__=='__main__':main()
