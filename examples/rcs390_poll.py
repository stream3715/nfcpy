#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-S390 Felica polling test.

Usage:
    python examples/rcs390_poll.py               # BLE スキャンで自動検出
    python examples/rcs390_poll.py AABBCCDDEEFF  # アドレス直指定 (BD_ADDR)
    python examples/rcs390_poll.py 246C0000-0000-1000-8000-00805F9B34FB
                                                   # macOS (CoreBluetooth) の場合は UUID を指定
    python examples/rcs390_poll.py -d ...        # デバッグログ付き
"""
import sys
import time
import logging
import argparse
import nfc
import nfc.clf


def main(args):
    logging.basicConfig(
        format='%(relativeCreated)6d ms [%(name)s] %(message)s',
        level=logging.DEBUG if args.debug else logging.WARNING,
    )

    path = "ble:{}".format(args.address) if args.address else "ble"

    print("RC-S390 に接続中... ({})".format(path))
    try:
        clf = nfc.ContactlessFrontend(path)
    except IOError as e:
        print("接続失敗:", e)
        sys.exit(1)

    print("接続完了: {}".format(clf))
    print("Felica カードを近づけてください (Ctrl+C で終了)\n")

    target_212f = nfc.clf.RemoteTarget("212F")
    target_424f = nfc.clf.RemoteTarget("424F")

    try:
        while True:
            target = clf.sense(target_212f, target_424f,
                               iterations=1, interval=0)
            if target:
                sensf_res = target.sensf_res
                idm  = sensf_res[1:9]
                pmm  = sensf_res[9:17]
                sysc = sensf_res[17:19] if len(sensf_res) >= 19 else None

                print("[{}] {} カード検出".format(
                    time.strftime("%H:%M:%S"), target.brty))
                print("  IDm : {}".format(idm.hex().upper()))
                print("  PMm : {}".format(pmm.hex().upper()))
                if sysc:
                    print("  Sys : {}".format(sysc.hex().upper()))
                print()
            else:
                print(".", end="", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n終了")
    finally:
        clf.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RC-S390 Felica polling test")
    parser.add_argument(
        "address", nargs="?", metavar="BLEADDR",
        help="BLE アドレス 12桁 hex、または macOS の場合は CoreBluetooth の"
             " UUID (省略でスキャン自動検出)")
    parser.add_argument(
        "-i", dest="interval", type=float, default=0.5, metavar="SEC",
        help="polling 間隔 秒 (default: 0.5)")
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="デバッグログ出力")
    main(parser.parse_args())
