#!/usr/bin/env python3
"""静态验证笔记包与逐页覆盖矩阵；不能替代学科内容核对。"""
import argparse,csv,re,sys
from pathlib import Path
ALLOWED={'已覆盖','非知识性页面','待人工核对','无法读取'}

def main():
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--strict',action='store_true');a=p.parse_args()
 d=Path(a.directory);errors=[];warnings=[]
 for x in ['00_课程导航.md','页码覆盖矩阵.csv','缺失与待核对清单.md']:
  if not (d/x).is_file():errors.append('缺少: '+x)
 notes=list((d/'课程笔记').glob('*.md')) if (d/'课程笔记').exists() else []
 if not notes:errors.append('没有课程笔记 MD')
 for f in notes:
  t=f.read_text(encoding='utf-8-sig')
  if not re.search(r'^# ',t,re.M) or not re.search(r'^## ',t,re.M):errors.append('标题层级不全: '+f.name)
  if '【待完善' in t or '第N页' in t:warnings.append('存在未完成占位: '+f.name)
  if not re.search(r'【来源：',t):warnings.append('没有逐知识点来源标记: '+f.name)
 matr=d/'页码覆盖矩阵.csv'
 if matr.exists():
  rows=list(csv.DictReader(matr.open(encoding='utf-8-sig',newline='')))
  if not rows:errors.append('覆盖矩阵为空')
  seen=set()
  for n,r in enumerate(rows,2):
   key=(r.get('source_file'),r.get('source_page'))
   if key in seen:errors.append(f'重复来源页: CSV行{n}: {key}')
   seen.add(key)
   st=r.get('status','')
   if st not in ALLOWED:errors.append(f'无效覆盖状态: CSV行{n}')
   if st in ('待人工核对','无法读取'):warnings.append(f'未完成覆盖: CSV行{n} {key}')
   if st in ('已覆盖','非知识性页面'):
    if st=='已覆盖' and not r.get('note_location'):errors.append(f'已覆盖但笔记定位为空: 行{n}')
    if st=='非知识性页面' and not r.get('remark'):errors.append(f'非知识性页面无理由: 行{n}')
    if st=='已覆盖' and r.get('note_location') and not (d/r['note_location']).exists():errors.append(f'笔记定位文件不存在: 行{n}')
 print('ERROR',len(errors),'WARN',len(warnings))
 for s in errors:print('ERROR:',s)
 for s in warnings[:35]:print('WARN:',s)
 if len(warnings)>35:print('...另有',len(warnings)-35,'项WARN')
 return 1 if errors or a.strict and warnings else 0
if __name__=='__main__':sys.exit(main())
