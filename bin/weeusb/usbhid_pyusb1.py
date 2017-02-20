# Copyright (c) 2017 Matthew Wall
# See the file LICENSE.txt for your rights.
"""USB HID abstraction using pyusb 1.x"""

import usb.core
import usb.util
import weewx

from weeusb import logdbg, loginf, logerr, USBHIDbase


class USBHID(USBHIDbase):
    def __init__(self, vendor_id, product_id):
        super(USBHID, self).__init__(vendor_id, product_id)
        self.iface = 0
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

        # be sure kernel does not claim the interface on linux systems
        try:
            self.dev.detach_kernel_driver(self.iface)
        except (AttributeError, usb.core.USBError, NotImplementedError), e:
            logdbg("Detach failed: %s" % e)

        # attempt to claim the interface
        try:
            self.dev.set_configuration()
            usb.util.claim_interface(self.dev, self.iface)
        except usb.core.USBError, e:
            self.close()
            msg = "Unable to claim USB interface %s: %s" % (self.iface, e)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)

    def close(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.iface)
            except (ValueError, usb.core.USBError), e:
                logerr("Release interface failed: %s" % e)
            self.dev = None

    def _reset(self):
        # use a usb reset to restore communication with the station.
        # specific cases include when you do an interrupt write with bogus
        # data.  use a reset to bring the station back to responsiveness.
        for x in range(5):
            try:
                self.dev.reset()
                break
            except usb.core.USBError, e:
                logdbg("USB reset failed: %s" % e)
                time.sleep(2)

    def _write(self, buf, reqtype=None, req=None, wval=None, timeout=50):
        if reqtype is None:
            reqtype = usb.util.build_request_type(
                usb.util.ENDPOINT_OUT,
                usb.util.CTRL_TYPE_CLASS,
                usb.util.CTRL_RECIPIENT_INTERFACE)
        if req is None:
            req = usb.REQ_SET_CONFIGURATION
        if wval is None:
            wval = 0x200
        return self.dev.ctrl_transfer(
            bmRequestType=reqtype,
            bRequest=req,
            data_or_wLength=buf,
            wValue=wval,
            timeout=timeout)

    def _read(self, sz, timeout=1000, endpoint_in=usb.util.ENDPOINT_IN):
        return self.dev.read(endpoint_in, sz, timeout)

    @staticmethod
    def _find_dev(vendor_id, product_id):
        return usb.core.find(idVendor=vendor_id, idProduct=product_id)

    @staticmethod
    def get_usb_info():
        v = 'unknown'
        try:
            v = usb.__version__
        except AttributeError:
            pass
        return "pyusb_version=%s" % v

    @staticmethod
    def is_non_error(e):
        return False
