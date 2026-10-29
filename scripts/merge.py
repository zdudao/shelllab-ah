#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并玩家投稿的拍卖行数据包，生成总表 prices.csv。

投稿包和总表用同一种格式，方便互相导入：
    # realm=Eversong Wilds faction=Alliance
    871,1793376000,88888888
    4411,1793376000,60000000

数据行三列：物品ID,日期(天级时间戳),价格(铜币)
"""
import os
import glob
import datetime

INCOMING = 'incoming'
OUT = 'prices.csv'

# 总表结构: {(realm, faction): {(item_id, day): price}}
data = {}


def load(path):
    """读一个 CSV（投稿包或已有总表），返回解析出的数据行数"""
    realm = None
    faction = ''
    n = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                # 元信息行：# realm=xxx faction=yyy ...
                seg = line[1:]
                for part in seg.split():
                    if part.startswith('realm='):
                        realm = part[len('realm='):]
                    elif part.startswith('faction='):
                        faction = part[len('faction='):]
                continue
            parts = line.split(',')
            if len(parts) != 3:
                continue  # 坏行直接跳过，不因一行坏数据整批失败
            try:
                item = int(parts[0])
                day = int(parts[1])
                price = int(parts[2])
            except ValueError:
                continue
            if realm is None:
                continue
            data.setdefault((realm, faction), {})[(item, day)] = price
            n += 1
    return n


def save():
    """写出总表，按服务器/阵营分组"""
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    lines = ['# ShellLab 拍卖行总表 v1',
             '# 更新时间=%s 记录数=%d' % (now, sum(len(v) for v in data.values()))]
    for key in sorted(data.keys()):
        realm, faction = key
        lines.append('# realm=%s faction=%s' % (realm, faction))
        rows = data[key]
        for (item, day), price in sorted(rows.items()):
            lines.append('%d,%d,%d' % (item, day, price))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    total_new = 0
    files = sorted(glob.glob(os.path.join(INCOMING, '*.csv')))
    files += sorted(glob.glob(os.path.join(INCOMING, '*.txt')))

    # 先读已有总表，再叠加投稿
    if os.path.exists(OUT):
        base = load(OUT)
        print('已有总表记录: %d' % base)
    else:
        print('尚无总表，从零开始')

    if not files:
        print('incoming/ 里没有新投稿')
    for p in files:
        n = load(p)
        print('  合并 %s -> %d 行' % (os.path.basename(p), n))
        total_new += n

    if files or not os.path.exists(OUT):
        save()
        print('已写出 %s，总记录 %d' % (OUT, sum(len(v) for v in data.values())))

    # 清掉已处理的投稿，避免重复合并
    for p in files:
        try:
            os.remove(p)
        except OSError:
            pass
    print('本次新增解析行数: %d' % total_new)


if __name__ == '__main__':
    main()
