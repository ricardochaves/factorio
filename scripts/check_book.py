import sys, re, time, bp, sim
def main(path, flt=None, maxent=800):
    d = bp.decode(open(path).read())
    for p, b in bp.walk(d):
        label = b.get('label') or ''
        if flt and not re.search(flt, ' / '.join(map(str,p))): continue
        if len(b.get('entities', [])) > maxent or len(b.get('entities', [])) < 3: continue
        m = re.match(r'\s*(\d+)\s*(?:to|-|_)\s*(\d+)', label)
        try:
            g = sim.parse_blueprint(b)
        except Exception as ex:
            print(f'{label:32s} PARSE-ERR {ex}'); continue
        t=time.time(); r = sim.check_balancer(g, n_random=15)
        exp = (int(m.group(1)), int(m.group(2))) if m else None
        shape_ok = exp == (r['N'], r['M'])
        print(f"{label:32s} {r['N']:>3}->{r['M']:<3} shape={'ok' if shape_ok else 'BAD'} ok={r['ok']!s:5} full={r['full_tp']:.3f} "
              f"outErr={r['out_balance_err']:.1e} inErr={r['in_balance_err']:.1e} defIn={r['tp_deficit_inputs_partial']:.2f} defOut={r['tp_deficit_outputs_partial']:.2f} "
              f"spl={len(g.splitters)} {time.time()-t:.1f}s {'W:'+str(len(r['warnings'])) if r['warnings'] else ''}")
main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
