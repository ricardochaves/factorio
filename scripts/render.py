"""ASCII renderer for belt blueprints."""
ARW = {0: '^', 4: '>', 8: 'v', 12: '<'}
UGI = {0: 'n', 4: 'e', 8: 's', 12: 'w'}     # underground input (lowercase)
UGO = {0: 'N', 4: 'E', 8: 'S', 12: 'W'}     # underground output (uppercase)
def render(b):
    cells = {}
    for e in b['entities']:
        d = e.get('direction', 0); x, y = e['position']['x'], e['position']['y']; n = e['name']
        if n.endswith('transport-belt'): cells[(int(x-.5), int(y-.5))] = ARW[d]
        elif n.endswith('underground-belt'):
            cells[(int(x-.5), int(y-.5))] = (UGI if e.get('type','input') == 'input' else UGO)[d]
        elif n.endswith('splitter'):
            ch = {0:'A',4:'}',8:'V',12:'{'}[d]
            if d in (0, 8): ts = [(int(round(x-1)), int(y-.5)), (int(round(x)), int(y-.5))]
            else: ts = [(int(x-.5), int(round(y-1))), (int(x-.5), int(round(y)))]
            for t in ts: cells[t] = ch
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
    out = []
    for y in range(min(ys), max(ys)+1):
        out.append(''.join(cells.get((x, y), '.') for x in range(min(xs), max(xs)+1)))
    return '\n'.join(out)
if __name__ == '__main__':
    import sys, bp
    d = bp.decode(open(sys.argv[1]).read())
    for p, b in bp.walk(d):
        if b.get('label') == sys.argv[2]:
            print(render(b)); break
