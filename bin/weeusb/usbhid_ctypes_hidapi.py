# Copyright (c) 2017 Matthew Wall
# See the file LICENSE.txt for your rights.
"""USB HID abstraction using ctypes hidapi"""

import ctypes
from ctypes.util import find_library
import weewx

from weeusb import logdbg, loginf, logerr, USBHIDbase

path = find_library('hidapi')
if not path:
    path = find_library('hidapi-libusb')
if not path:
    path = find_library('hidapi-hidraw')
if not path:
    raise ImportError('Cannot find hidapi library')
hidapi = ctypes.CDLL(path)
hidapi.hid_open.argtypes = [
    ctypes.c_ushort, ctypes.c_ushort, ctypes.c_wchar_p]
hidapi.hid_open.restype = ctypes.c_void_p
hidapi.hid_read_timeout.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
hidapi.hid_write.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]


class USBHID(USBHIDbase):
    def __init__(self, vendor_id, product_id, iface=0):
        super(USBHID, self).__init__(vendor_id, product_id, iface)
        self.dev = None
        loginf(USBHID.get_usb_info())

    def open(self):
        dev = USBHID._find_dev(self.vendor_id, self.product_id)
        if dev:
            loginf("Found USB device with VendorID=0x%04x ProductID=0x%04x" %
                   (self.vendor_id, self.product_id))
        else:
            msg = "Cannot find USB device with " \
                "VendorID=0x%04x ProductID=0x%04x" % \
                (self.vendor_id, self.product_id)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)
        self.dev = dev

    def close(self):
        if self.dev:
            self.dev = None

    def _write(self, buf, reqtype=None, req=None, wval=None, timeout=50):
        data = ''.join(map(chr, buf))
        return hidapi.hid_write(self.dev, ctypes.c_char_p(data), len(data))

    def _read(self, sz, timeout=100, endpoint_in=None):
        result = list()
        data = ctypes.create_string_buffer(8)
        while sz > 0:
            cnt = min(sz, 8)
            n = hidapi.hid_read_timeout(self.dev, data, cnt, timeout)
            if n <= 0:
                return result # short read
            for i in range(n):
                result.append(ord(data[i]))
            sz -= n
        return result

    @staticmethod
    def _find_dev(vendor_id, product_id):
        return hidapi.hid_open(vendor_id, product_id)

    @staticmethod
    def get_usb_info():
        return "hidapi_version=unknown"

    @staticmethod
    def is_non_error(e):
        return False
