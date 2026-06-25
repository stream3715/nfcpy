# -*- coding: latin-1 -*-
# -----------------------------------------------------------------------------
# Copyright 2021, 2021 Oliet Lunata <oliet2357@gmail.com>
#
# Licensed under the EUPL, Version 1.1 or - as soon they
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
#
# https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.
# -----------------------------------------------------------------------------
"""BLE Wrapper module for contactless devices based on the Sony NFC Port-100
chipset. The only product known to use this chipset in BLE is the PaSoRi RC-S390.
RC-S390 was an outer Felica reader for iOS. It supports reading and writing
of Type F tags.

==========  =======  ============
function    support  remarks
==========  =======  ============
sense_tta   no
sense_ttb   no
sense_ttf   yes      slow (BLE)
sense_dep   no
listen_tta  no
listen_ttb  no
listen_ttf  no
listen_dep  no
==========  =======  ============

"""
import nfc.clf
from . import device
from . import rcs380

import logging
log = logging.getLogger(__name__)

READ_UUID = "233e8101-3a1b-1c59-9bee-180373dd03a1"
DUMMY_UUID = "233e8102-3a1b-1c59-9bee-180373dd03a1"
WRITE_UUID = "233e8103-3a1b-1c59-9bee-180373dd03a1"


class Device(device.Device):
    @property
    def vendor_name(self):
        return self.port100._vendor_name if hasattr(self.port100, "_vendor_name") else ''

    @property
    def product_name(self):
        return self.port100._device_name if hasattr(self.port100, "_device_name") else ''

    @property
    def chipset_name(self):
        return self.port100._chipset_name

    def __init__(self, port100, logger=None):
        self.port100 = port100
        self.log = logger or log

    def close(self):
        try:
            return self.port100.close()
        except IOError:
            pass

    def mute(self):
        return self.port100.mute()

    def sense_tta(self, target):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support Type A")

    def sense_ttb(self, target):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support Type B")

    def sense_ttf(self, target):
        return self.port100.sense_ttf(target)

    def sense_dep(self, target):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support DEP")

    def listen_tta(self, target, timeout):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support listen Type A")

    def listen_ttb(self, target, timeout):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support listen Type B")

    def listen_ttf(self, target, timeout):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support listen Type F")

    def listen_dep(self, target, timeout):
        raise nfc.clf.UnsupportedTargetError("RC-S390 does not support listen DEP")

    def get_max_send_data_size(self, target):
        return self.port100.get_max_send_data_size(target)

    def get_max_recv_data_size(self, target):
        return self.port100.get_max_recv_data_size(target)

    def send_cmd_recv_rsp(self, target, data, timeout):
        return self.port100.send_cmd_recv_rsp(target, data, timeout)

    def _tt2_send_cmd_recv_rsp(self, data, timeout_msec):
        return self.port100._tt2_send_cmd_recv_rsp(data, timeout_msec)

    def send_rsp_recv_cmd(self, target, data, timeout):
        return self.port100.send_rsp_recv_cmd(target, data, timeout)


def init(transport):
    transport.notify_only(READ_UUID)
    transport.notify_only(DUMMY_UUID)
    transport.read_uuid = READ_UUID
    transport.write_uuid = WRITE_UUID
    device = Device(rcs380.init(transport, logger=log, command_type=3), logger=log)
    device._vendor_name = 'Sony'
    device._device_name = 'RC-S390'
    return device
