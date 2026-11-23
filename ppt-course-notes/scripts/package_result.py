#!/usr/bin/env python3
"""将一次任务的最终输出目录打成 ZIP，禁止把技能定义或临时材料混入。"""
import argparse,os,zipfile
from pathlib import Path
EXCLUDE={'.git','__pycache__','_source_unpacked','.scratch','.work','.DS_Store'}
BAD_EXT={'.pyc','.tmp','.bak'}
def run():
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',required=True);a=p.parse_args()
 src=Path(a.directory).resolve();out=Path(a.output).resolve()
 if not src.is_dir():p.error('directory 必须是现有文件夹')
 if src==out.parent or src in out.parents:p.error('请将输出ZIP放在目录外部，避免递归打包')
 fs=[f for f in src.rglob('*') if f.is_file() and f.resolve()!=out and not EXCLUDE.intersection(f.relative_to(src).parts)
     and f.suffix.lower() not in BAD_EXT and f.name!='SKILL.md']
 if not fs:p.error('没有可打包的最终文件')
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for f in sorted(fs):z.write(f,arcname=str(Path(src.name)/f.relative_to(src)).replace('\\','/'))
 with zipfile.ZipFile(out) as z:
  errors=z.testzip();assert errors is None,errors
  members=[m for m in z.namelist() if not m.endswith('/')]
  assert members and all(m.startswith(src.name+'/') for m in members)
 print(f'ZIP校验通过，共{len(members)}个文件: {out}')
if __name__=='__main__':run()
