#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-S390 Felica card dumper.

Usage:
    python examples/rcs390_dump.py               # BLE スキャンで自動検出
    python examples/rcs390_dump.py AABBCCDDEEFF  # アドレス直指定
    python examples/rcs390_dump.py -d ...        # デバッグログ付き
"""
import sys
import struct
import logging
import argparse
import nfc
import nfc.clf
from nfc.tag.tt3 import ServiceCode, Type3TagCommandError


def request_system_code(tag):
    """Request System Code (0x0C) でカード上の全システムコード取得。"""
    try:
        # レスポンス: [N, SC0_hi, SC0_lo, SC1_hi, SC1_lo, ...]
        data = tag.send_cmd_recv_rsp(0x0C, b'', 0.5, check_status=False)
        n = data[0]
        return [struct.unpack('>H', data[1+i*2:3+i*2])[0] for i in range(n)]
    except Exception:
        return [tag.sys]


def search_services(tag):
    """Search Service Code (0x0A) でサービスコード一覧取得。"""
    services = []
    for idx in range(0x10000):
        try:
            # レスポンス: [SC_lo, SC_hi] (0xFFFF = 終端)
            data = tag.send_cmd_recv_rsp(
                0x0A, struct.pack('<H', idx), 0.5, check_status=False)
            sc_raw = struct.unpack('<H', data[:2])[0]
            if sc_raw == 0xFFFF:
                break
            services.append(sc_raw)
        except Exception:
            break
    return services


def dump_card(tag):
    print("IDm : {}".format(tag.idm.hex().upper()))
    print("PMm : {}".format(tag.pmm.hex().upper()))
    print("SYS : {:04X}".format(tag.sys))

    sys_codes = request_system_code(tag)
    print("Systems: [{}]".format(', '.join('{:04X}'.format(s) for s in sys_codes)))

    for sc in sys_codes:
        print("\n=== System {:04X} ===".format(sc))

        # このシステムに re-poll してアクティブ化
        try:
            result = tag.polling(sc, request_code=0)
            tag.idm = bytearray(result[0])
            tag.sys = sc
        except Exception as e:
            print("  (polling failed: {})".format(e))
            continue

        services = search_services(tag)
        if not services:
            print("  (no services)")
            continue

        print("  Services: [{}]".format(', '.join('{:04X}'.format(s) for s in services)))

        for svc_raw in services:
            svc = ServiceCode(svc_raw >> 6, svc_raw & 0x3F)
            print("\n  Service {:04X}:".format(svc_raw))
            try:
                lines = tag.dump_service(svc)
                for line in lines:
                    print("    {}".format(line))
            except Type3TagCommandError as e:
                print("    (access denied or empty: {})".format(e))
            except Exception as e:
                print("    (error: {})".format(e))


def main(args):
    logging.basicConfig(
        format='%(relativeCreated)6d ms [%(name)s] %(message)s',
        level=logging.DEBUG if args.debug else logging.WARNING,
    )

    path = "ble:{}".format(args.address) if args.address else "ble"
    print("RC-S390 接続中... ({})".format(path))

    try:
        clf = nfc.ContactlessFrontend(path)
    except IOError as e:
        print("接続失敗:", e)
        sys.exit(1)

    print("接続完了: {}".format(clf))
    print("Felica カードを近づけてください (Ctrl+C で終了)\n")

    def on_connect(tag):
        print("[カード検出] {} @ {}".format(tag.type, tag.brty if hasattr(tag, 'brty') else '?'))
        try:
            dump_card(tag)
        except Exception as e:
            print("ダンプエラー:", e)
        return False

    try:
        while True:
            clf.connect(rdwr={
                'on-connect': on_connect,
                'targets': ['212F', '424F'],
                'iterations': 5,
                'interval': 0.2,
            })
    except KeyboardInterrupt:
        print("\n終了")
    finally:
        clf.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RC-S390 Felica card dump")
    parser.add_argument(
        "address", nargs="?", metavar="BLEADDR",
        help="BLE アドレス 12桁 hex (省略でスキャン自動検出)")
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="デバッグログ出力")
    main(parser.parse_args())
