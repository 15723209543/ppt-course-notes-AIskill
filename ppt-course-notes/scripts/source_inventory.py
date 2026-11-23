#!/usr/bin/env python3
"""对用户本次课件/作业/复习资料做可审计的来源清点，不尝试生成答案。
可选依赖: python-pptx, python-docx, pymupdf; 没有依赖时记录未读取，不伪装成功。
用法: python source_inventory.py --input <目录或文件或zip> --output <清单.json> [--extract-dir <目录>]
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys, zipfile
from pathlib import Path

TEXT_EXT={'.md','.txt','.csv','.tex','.py','.java','.c','.cpp','.h','.json'}
IMG_EXT={'.jpg','.jpeg','.png','.webp','.bmp','.gif'}
DOC_EXT={'.pdf','.ppt','.pptx','.docx','.doc','.odt','.odp'}
SKIP_DIR={'.git','__pycache__','.venv','node_modules'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def extract_safe(zpath,out):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir():continue
            nm=info.filename.replace('\\','/')
            part=Path(nm)
            if part.is_absolute() or '..' in part.parts or ':' in nm or len(part.parts)>20:
                raise ValueError('ZIP存在不安全路径: '+nm)
            if any(s in SKIP_DIR or s.startswith('.') and s != '.' for s in part.parts):continue
            # 避免巨型 ZIP 炸弹
            if info.file_size>128*1024*1024:raise ValueError('ZIP单文件超过128MiB: '+nm)
            dest=out.joinpath(*part.parts)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst)

def inspect(p,relative):
    item={'file':relative,'type':p.suffix.lower(),'sha256':digest(p),'bytes':p.stat().st_size,
          'page_unit':None,'pages':[],'warnings':[],'status':'ok'}
    ext=p.suffix.lower()
    try:
        if ext=='.pptx':
            from pptx import Presentation
            pres=Presentation(str(p))
            item['page_unit']='幻灯片'
            for i,sl in enumerate(pres.slides,1):
                seg=[]; has_visual=False
                for sh in sorted(sl.shapes,key=lambda x:(x.top,x.left)):
                    if sh.has_text_frame and sh.text.strip():seg.append(sh.text)
                    if sh.has_table:
                        for row in sh.table.rows:
                            seg.append(' | '.join(c.text for c in row.cells))
                    if sh.shape_type==13 or sh.shape_type==6:has_visual=True
                    if getattr(sh,'has_chart',False):has_visual=True
                # 讲稿属于额外信息，避免未经核对混入授课正文
                item['pages'].append({'number':i,'text':'\n'.join(seg),'has_visual':has_visual})
        elif ext=='.pdf':
            import fitz
            doc=fitz.open(str(p)); item['page_unit']='PDF页'
            for i,pg in enumerate(doc,1):
                item['pages'].append({'number':i,'text':pg.get_text('text'),
                                      'has_visual':bool(pg.get_images(full=True))})
            doc.close()
        elif ext=='.docx':
            from docx import Document
            doc=Document(str(p)); item['page_unit']='整份文档（未提供可靠物理页码）'
            txt=[x.text for x in doc.paragraphs if x.text.strip()]
            for tbl in doc.tables:
                for row in tbl.rows: txt.append(' | '.join(c.text for c in row.cells))
            item['pages']=[{'number':None,'text':'\n'.join(txt),'has_visual':len(doc.inline_shapes)>0}]
        elif ext in TEXT_EXT:
            item['page_unit']='整份文本（无可靠物理页码）'
            raw=p.read_bytes()
            try: txt=raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                txt=raw.decode('gbk')
                item['warnings'].append('文本采用GBK解码，请核实')
            item['pages']=[{'number':None,'text':txt,'has_visual':False}]
        elif ext in IMG_EXT:
            item['status']='visual_review_required';item['page_unit']='图片'
            item['pages']=[{'number':None,'text':'','has_visual':True}]
            item['warnings'].append('图片未自动识字，必须用视觉阅读核对题目/公式/表格')
        elif ext in {'.ppt','.doc','.odt','.odp'}:
            item['status']='unsupported_format'
            item['warnings'].append('旧格式须用原生应用另存为pptx/docx或可靠转换后重新清点；不得虚构内容')
        else:
            item['status']='unsupported_format';item['warnings'].append('不在自动解析范围')
    except ImportError as e:
        item['status']='missing_dependency';item['warnings'].append(f'缺少读取依赖: {e.name}')
    except Exception as e:
        item['status']='parse_failed';item['warnings'].append(f'解析失败: {type(e).__name__}: {e}')
    return item

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True,help='源文件、源目录或ZIP')
    ap.add_argument('--output',required=True,help='清单 JSON 输出路径')
    ap.add_argument('--extract-dir',help='ZIP解压位置，默认清单同级的 _source_unpacked/')
    a=ap.parse_args(); src=Path(a.input).expanduser().resolve(); out=Path(a.output).expanduser().resolve()
    if not src.exists():ap.error(f'输入不存在: {src}')
    if src.suffix.lower()=='.zip':
        root=Path(a.extract_dir).resolve() if a.extract_dir else out.parent/'_source_unpacked'
        extract_safe(src,root)
        paths=[p for p in root.rglob('*') if p.is_file() and not SKIP_DIR.intersection(p.parts)]
    elif src.is_dir():
        root=src;paths=[p for p in root.rglob('*') if p.is_file() and not SKIP_DIR.intersection(p.parts)]
    else:
        root=src.parent;paths=[src]
    paths=sorted((p for p in paths if p.resolve()!=out),key=lambda x:str(x.relative_to(root)).casefold())
    records=[inspect(p,str(p.relative_to(root)).replace('\\','/')) for p in paths]
    counts={}
    for x in records:counts[x['status']]=counts.get(x['status'],0)+1
    result={'schema':'teaching-source-inventory/v1','input_name':src.name,
            'sources':records,'summary':{'files':len(records), 'status_counts':counts,
            'slides_or_pdf_pages':sum(len(x['pages']) for x in records if x['page_unit'] in ('幻灯片','PDF页'))},
            'caution':'只有逐项读取与人工核对后，才可断言已完整覆盖。图形公式/图片题目必须视觉核对。'}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"清点 {len(records)} 个文件；状态 {counts}；结果: {out}")
    return 0
if __name__=='__main__':sys.exit(main())
