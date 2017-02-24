# Copyright (c) 2017 Matthew Wall
# See the file LICENSE.txt for your rights.
"""USB HID abstraction using cython hid"""

import hid
import weewx

from weeusb import logdbg, loginf, logerr, USBHIDbase

# FIXME: set nonblocking = 1

class USBHID(USBHIDbase):
    def __init__(self, vendor_id, product_id):
        super(USBHID, self).__init__(vendor_id, product_id)
        self.dev = None
        loginf(USBHID.get_usb_info())

    def open(self):
        dev = USBHID._find_dev(self.vendor_id, self.product_id)
        if not dev:
            msg = "Cannot find USB device with " \
                "VendorID=0x%04x ProductID=0x%04x" % \
                (self.vendor_id, self.product_id)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)
        loginf("Found USB device with VendorID=0x%04x ProductID=0x%04x" %
               (self.vendor_id, self.product_id))
        self.dev = dev
        self.dev.open(self.vendor_id, self.product_id)

    def close(self):
        if self.dev:
            self.dev.close()
            self.dev = None

    def _write(self, buf, reqtype=None, req=None, wval=None, timeout=50):
        return self.dev.write(buf)

    def _read(self, sz, timeout=1000, endpoint_in=None):
        return self.dev.read(sz, timeout_ms=timeout)

    @staticmethod
    def _find_dev(vendor_id, product_id):
        if hid.enumerate(vendor_id, product_id):
            return hid.device(vendor_id, product_id)
        return None

    @staticmethod
    def get_usb_info():
        v = 'unknown'
        try:
            v = hid.sys.version.replace('\n', ' ')
        except AttributeError:
            pass
        return "cython_hid_version=%s" % v

    @staticmethod
    def is_non_error(e):
        return False
