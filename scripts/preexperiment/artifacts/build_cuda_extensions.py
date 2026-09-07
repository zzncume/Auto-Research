import os,subprocess,sys,shutil,json
from pathlib import Path
os.environ.update(CUDA_HOME='/work/cuda-12.1',FORCE_CUDA='1',TORCH_CUDA_ARCH_LIST='8.0',MAX_JOBS='2',CC='/usr/bin/x86_64-linux-gnu-gcc-11',CXX='/usr/bin/x86_64-linux-gnu-g++-11',CUB_HOME='/work/cuda-12.1/include')
os.environ['PATH']=str(Path(sys.executable).parent)+':/work/cuda-12.1/bin:/usr/bin:/bin'
includes=sorted((Path(sys.prefix)/'lib/python3.11/site-packages/nvidia').glob('*/include'))
os.environ['CPATH']=':'.join(map(str,includes))
os.environ['NVCC_FLAGS']='-gencode=arch=compute_80,code=sm_80 '+' '.join('-I'+str(p) for p in includes)
work=Path('/work');out=work/('wheels-sm80' if sys.argv[1]=='pytorch3d' else 'wheels');out.mkdir(exist_ok=True)
source=next(work.glob(sys.argv[1]+'-*'))
if sys.argv[1]=='gsplat':
 glm=next(work.glob('glm-*'));target=source/'gsplat/cuda/csrc/third_party/glm'
 shutil.copytree(glm,target,dirs_exist_ok=True)
r=subprocess.run([sys.executable,'setup.py','bdist_wheel','--dist-dir',str(out)],cwd=source)
raise SystemExit(r.returncode)
