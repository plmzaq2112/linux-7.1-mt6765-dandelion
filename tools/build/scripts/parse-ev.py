import struct

data = open('/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/logs/diag/ev.bin', 'rb').read()
n = len(data) // 24
syn = 0
abs_ev = 0
ts = []
for i in range(n):
    tv_s, tv_us, typ, code, val = struct.unpack('<qqHHi', data[i*24:(i+1)*24])
    if typ == 0 and code == 0:
        syn += 1
        ts.append(tv_s + tv_us / 1e6)
    if typ == 3:
        abs_ev += 1

print('events', n, 'abs', abs_ev, 'syn', syn)
if len(ts) > 2:
    dur = ts[-1] - ts[0]
    print('duration %.2fs  frames %d  rate %.1f Hz' % (dur, syn - 1, (syn - 1) / dur if dur > 0 else 0))
    gaps = [ts[i+1] - ts[i] for i in range(len(ts) - 1)]
    gaps_sorted = sorted(gaps)
    med = gaps_sorted[len(gaps_sorted) // 2]
    print('min gap %.1f ms  median %.1f ms  max %.1f ms' % (min(gaps)*1000, med*1000, max(gaps)*1000))
