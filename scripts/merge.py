#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并玩家投稿的拍卖行数据包，生成总表 prices.csv。

投稿包和总表用同一种格式，方便互相导入：
    # realm=Eversong Wilds
    # faction=Alliance
    871,1793376000,88888888
    4411,1793376000,60000000

注意：服务器名可能带空格（Eversong Wilds / Basin of Stars），
所以 realm 和 faction 必须各占一行，不能写在一行里用空格分隔。
数据行三列：物品ID,日期(天级时间戳),价格(铜币)
"""
import os
import glob
import datetime

INCOMING = 'incoming'
OUT = 'prices.csv'

# 总表结构: {(realm, faction): {(item_id, day): price}}
data = {}


def read_meta(line):
    """解析一行元信息（# 开头），返回 (key, value) 或 None。"""
    seg = line[1:].strip()
    if seg.startswith('realm='):
        v = seg[len('realm='):].strip()
        # 兼容旧格式：一行里同时写了 faction=
        i = v.rfind(' faction=')
        if i >= 0:
            return ('realm_both', (v[:i].strip(), v[i + len(' faction='):].strip()))
        return ('realm', v)
    if seg.startswith('faction='):
        return ('faction', seg[len('faction='):].strip())
    return None


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
                # 元信息行：# realm=xxx / # faction=yyy
                meta = read_meta(line)
                if meta:
                    key, val = meta
                    if key == 'realm':
                        realm = val
                    elif key == 'faction':
                        faction = val
                    elif key == 'realm_both':
                        realm, faction = val
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
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = ['# ShellLab 拍卖行总表 v1',
             '# 更新时间=%s 记录数=%d' % (now, sum(len(v) for v in data.values()))]
    for key in sorted(data.keys()):
        realm, faction = key
        lines.append('# realm=%s' % realm)
        lines.append('# faction=%s' % faction)
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
