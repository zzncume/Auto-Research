"""Plot numeric metrics supplied by the researcher, when available."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--metric');p.add_argument('--output',default='experiment_metrics.png')
    a=p.parse_args();rows=[]
    for f in sorted(Path('.').glob('run_*/final_info.json')):
        metrics=json.loads(f.read_text()).get('system_defined_metrics',{})
        if not isinstance(metrics,dict):continue
        for key,value in metrics.items():
            if (a.metric is None or key==a.metric) and type(value) in (int,float):rows.append((f.parent.name,key,value))
    if not rows:
        print('No system-defined numeric metrics available; no plot generated.');return
    import matplotlib.pyplot as plt
    keys=sorted({key for _,key,_ in rows});fig,axes=plt.subplots(len(keys),1,squeeze=False,figsize=(7,4*len(keys)))
    for ax,key in zip(axes[:,0],keys):
        selected=[(name,value) for name,k,value in rows if k==key]
        ax.bar([x[0] for x in selected],[x[1] for x in selected]);ax.set_ylabel(key)
    fig.tight_layout();fig.savefig(a.output)
if __name__=='__main__':main()
