#!/usr/bin/env python3
"""从来源清单创建笔记目录和逐页覆盖矩阵；待 AI 填写正文并逐页核对。"""
import argparse, csv, json,re
from pathlib import Path

def safe(s):
 s=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',s).strip(' .')
 return s[:75] or '未命名'

def main():
 p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 data=json.loads(Path(a.inventory).read_text(encoding='utf-8'))
 out=Path(a.output).resolve();notes=out/'课程笔记';notes.mkdir(parents=True,exist_ok=True)
 rows=[];index=['# 课程笔记导航','','> 当前文件是骨架；需根据上传原始课件逐页填写与核对。','','| 序号 | 来源文件 | 页数 | 状态 | 笔记 |','|---|---|---:|---|---|']
 for k,f in enumerate(data['sources'],1):
  if f['type'] not in {'.pptx','.pdf','.ppt'}:continue
  fn=f'{k:02d}_{safe(Path(f["file"]).stem)}_笔记.md'
  pth=notes/fn
  if pth.exists():raise SystemExit('目标文件已存在，停止覆盖: '+str(pth))
  pth.write_text(f'# {Path(f["file"]).stem}\n\n> 来源：`{f["file"]}`；仅为待填写的笔记骨架。\n\n## 本章学习目标\n\n【待完善：结合本次课件填写】\n\n## 本章知识点\n\n### 知识点一\n\n**定义：** 【待完善】\n\n**性质/结论与用法：** 【待完善】\n\n**例题与易错点：** 【待完善】\n\n【来源：{f["file"]}｜第N页（请替换为真实页码）】\n\n## 本章核心结论\n\n【待完善】\n',encoding='utf-8')
  index.append(f'| {k} | `{f["file"]}` | {len(f["pages"])} | {f["status"]} | [打开笔记](课程笔记/{fn}) |')
  for x in f['pages']:
   lines=' '.join(x['text'].split())
   rows.append({'source_file':f['file'],'source_unit':f['page_unit'] or '', 'source_page':x['number'] if x['number'] is not None else '',
    'source_excerpt':lines[:140], 'status':'待人工核对' if f['status']=='ok' else '无法读取',
    'note_location':f'课程笔记/{fn}','remark':'有图形，需视觉核对' if x['has_visual'] else '; '.join(f['warnings'])})
  if not f['pages']:
   rows.append({'source_file':f['file'],'source_unit':'','source_page':'','source_excerpt':'',
    'status':'无法读取','note_location':f'课程笔记/{fn}','remark':'; '.join(f['warnings'])})
 (out/'00_课程导航.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
 (out/'缺失与待核对清单.md').write_text('# 缺失与待核对清单\n\n> 按真实检查结果逐项填写。\n\n',encoding='utf-8')
 with (out/'页码覆盖矩阵.csv').open('w',encoding='utf-8-sig',newline='') as fp:
  wr=csv.DictWriter(fp,fieldnames=['source_file','source_unit','source_page','source_excerpt','status','note_location','remark']);wr.writeheader();wr.writerows(rows)
 print(f'生成 {len(rows)} 行覆盖索引；{len(list(notes.glob("*.md")))} 份笔记骨架：{out}')
if __name__=='__main__':main()
