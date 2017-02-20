# Copyright (c) 2017 Matthew Wall
# See the file LICENSE.txt for your rights.
"""USB HID abstraction using libusb 1.x"""

import libusb1
import usb1
import weewx

from weeusb import logdbg, loginf, logerr, USBHIDbase


class USBHID(USBHIDbase):
    def __init__(self, vendor_id, product_id):
        super(USBHID, self).__init__(vendor_id, product_id)
        self.iface = 0
        self.context = None
        loginf(USBHID.get_usb_info())

    def open(self):
        dev = USBHID._find_dev(self.vendor_id, self.product_id)
        if dev:
            loginf("Found USB device with VendorID=0x%04x ProductID=0x%04x" %
                   (vendor_id, product_id))
        else:
            msg = "Cannot find USB device with " \
                "VendorID=0x%04x ProductID=0x%04x" % \
                (self.vendor_id, self.product_id)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)
        self.dev = dev

        # be sure kernel does not claim the interface on linux systems
        try:
            self.dev.detachKernelDriver(self.iface)
        except (AttributeError, usb.USBError, NotImplementedError), e:
            logdbg("Detach failed: %s" % e)

        # attempt to claim the interface
        try:
            self.devh.claimInterface(self.iface)
        except usb.USBError, e:
            self.close()
            msg = "Unable to claim USB interface %s: %s" % (self.iface, e)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)

    def close(self):
        if self.dev:
            try:
                self.dev.releaseInterface()
            except (ValueError, usb.USBError), e:
                logerr("Release interface failed: %s" % e)
            self.dev = None

    def _reset(self):
        # use a usb reset to restore communication with the station.
        # specific cases include when you do an interrupt write with bogus
        # data.  use a reset to bring the station back to responsiveness.
        for x in range(5):
            try:
                self.devh.reset()
                break
            except usb.USBError, e:
                logdbg("USB reset failed: %s" % e)
                time.sleep(2)

    def _write(self, buf, reqtype=None, req=None, wval=None, timeout=50):
        if reqtype is None:
            reqtype = libusb1.LIBUSB_ENDPOINT_OUT | \
                libusb1.LIBUSB_TYPE_CLASS | \
                libusb1.LIBUSB_RECIPIENT_INTERFACE
        if req is None:
            req = usb.REQ_SET_CONFIGURATION
        if wval is None:
            wval = 0x200
        strbuf = ''.join(map(chr, buf))
        return self.devh.controlMsg(
            reqtype,
            req,
            strbuf,
            value=wval,
            timeout=timeout)

    def _read(self, sz, timeout=1000, endpoint_in=usb.ENDPOINT_IN):
        buf = self.dev.bulkRead(endpoint_in, sz, timeout)
        return map(ord, buf)

    @staticmethod
    def _find_dev(vendor_id, product_id):
        context = usb1.USBContext()
        return context.openByVendorIDAndProductID(vendor_id, product_id)

    @staticmethod
    def get_usb_info():
        return 'libusb1_version=unknown'

    @staticmethod
    def is_non_error(e):
        return False
