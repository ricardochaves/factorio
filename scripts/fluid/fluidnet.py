"""Fluid network model for Factorio 2.0 base-game entities (blueprint JSON)."""
import json, collections, math

DIRS={0:(0,-1),4:(1,0),8:(0,1),12:(-1,0)}
def rot(off,d):  # rotate offset clockwise by d/4 quarter turns
    x,y=off
    for _ in range((d//4)%4): x,y=-y,x
    return (x,y)
def rdir(dd,d): return (dd+d)%16
OPP=lambda d:(d+8)%16

# (offset tile relative to center, direction, kind)  kind: 'io','in','out'
CONN={
 'pipe':[((0,0),0,'io'),((0,0),4,'io'),((0,0),8,'io'),((0,0),12,'io')],
 'storage-tank':[((-1,-1),0,'io'),((-1,-1),12,'io'),((1,1),4,'io'),((1,1),8,'io')],  # verified in game 2.0.77
 'chemical-plant':[((-1,-1),0,'in'),((1,-1),0,'in'),((-1,1),8,'out'),((1,1),8,'out')],
 'oil-refinery':[((-1,2),8,'in'),((1,2),8,'in'),((-2,-2),0,'out'),((0,-2),0,'out'),((2,-2),0,'out')],
 'assembling-machine-3':[((0,-1),0,'in'),((0,1),8,'out')],
 'pump':[((0,-0.5),0,'out'),((0,0.5),8,'in')],
}
SEG_ENT={'pipe','pipe-to-ground','storage-tank'}  # entities that are part of a segment (pumps/machines are boundaries)

def tiles_of(e):
    """tile keys of a pump connection: pump center is (x, y.5)."""
    pass

def build(ents):
    byid={e['entity_number']:e for e in ents}
    conns=collections.defaultdict(list)  # tile(int x,int y) -> list of (eid, dir, kind, port_index)
    ptg={}  # tile -> (eid, underground dir)
    for e in ents:
        n=e['name']; d=e.get('direction',0); px,py=e['position']['x'],e['position']['y']
        if n=='pipe-to-ground':
            t=(int(math.floor(px)),int(math.floor(py)))
            conns[t].append((e['entity_number'],d,'io',0))
            ptg[t]=(e['entity_number'],OPP(d))
            continue
        if n not in CONN: continue
        for i,(off,dd,kind) in enumerate(CONN[n]):
            ox,oy=rot(off,d)
            t=(int(math.floor(px+ox)),int(math.floor(py+oy)))
            conns[t].append((e['entity_number'],rdir(dd,d),kind,0 if n in SEG_ENT else i))
    # edges between ports: port=(eid,port_index)
    adj=collections.defaultdict(set)
    for t,lst in conns.items():
        for (eid,dd,kind,i) in lst:
            dx,dy=DIRS[dd]; nt=(t[0]+dx,t[1]+dy)
            for (eid2,dd2,kind2,i2) in conns.get(nt,[]):
                if dd2==OPP(dd) and eid2!=eid:
                    if 'in' in (kind,kind2) and 'out' in (kind,kind2) and byid[eid]['name']!='pump' and byid[eid2]['name']!='pump':
                        pass
                    adj[(eid,i)].add((eid2,i2)); adj[(eid2,i2)].add((eid,i))
    # underground links
    for t,(eid,ud) in ptg.items():
        dx,dy=DIRS[ud]
        for k in range(1,11):
            nt=(t[0]+dx*k,t[1]+dy*k)
            if nt in ptg:
                eid2,ud2=ptg[nt]
                if ud2%8!=ud%8: continue  # perpendicular pipe-to-ground does not block
                if ud2==OPP(ud):
                    adj[(eid,0)].add((eid2,0)); adj[(eid2,0)].add((eid,0))
                break  # same-axis ptg blocks
    # segments: union of SEG_ENT ports, plus attached machine/pump ports as members
    seg_of={}; segs=[]
    for e in ents:
        if e['name'] not in SEG_ENT: continue
        p=(e['entity_number'],0)
        if p in seg_of: continue
        sid=len(segs); members=set(); stack=[p]; ports=set()
        while stack:
            q=stack.pop()
            if q in seg_of: continue
            seg_of[q]=sid; members.add(q[0])
            for r in adj[q]:
                if byid[r[0]]['name'] in SEG_ENT:
                    if r not in seg_of: stack.append(r)
                else:
                    ports.add(r)
        segs.append({'id':sid,'ents':members,'ports':ports})
    # direct machine<->machine / pump<->machine links without pipes: create pseudo-segments
    for p,rs in list(adj.items()):
        if byid[p[0]]['name'] in SEG_ENT: continue
        for r in rs:
            if byid[r[0]]['name'] in SEG_ENT: continue
            key=tuple(sorted([p,r]))
            if key in seg_of: continue
            sid=len(segs); seg_of[key]=sid
            segs.append({'id':sid,'ents':set(),'ports':{p,r},'direct':True})
    return byid,conns,adj,segs,seg_of

def seg_ports_by_kind(seg,byid):
    out=collections.defaultdict(list)
    for (eid,i) in seg['ports']:
        e=byid[eid]; kind=CONN[e['name']][i][2]
        out[(e['name'],e.get('recipe'),kind)].append(eid)
    return out
