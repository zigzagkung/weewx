# Copyright (c) 2017 Matthew Wall
# See the file LICENSE.txt for your rights.
"""USB HID abstraction using pyusb 0.4"""

import time
import usb
import weewx

from weeusb import logdbg, loginf, logerr, USBHIDbase


class USBHID(USBHIDbase):
    def __init__(self, vendor_id, product_id):
        super(USBHID, self).__init__(vendor_id, product_id)
        self.iface = 0
        self.devh = None
        loginf(USBHID.get_usb_info())

    def open(self):
        dev, bus, devid = USBHID._find_dev(self.vendor_id, self.product_id)
        if dev:
            loginf("Found USB device with VendorID=0x%04x ProductID=0x%04x"
                   " on USB bus=%s device=%s" %
                   (self.vendor_id, self.product_id, bus, devid))
        else:
            msg = "Cannot find USB device with " \
                "VendorID=0x%04x ProductID=0x%04x" % \
                (self.vendor_id, self.product_id)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)

        self.devh = dev.open()
        if not self.devh:
            raise weewx.WeeWxIOError('Open failed for USB device')

        # be sure kernel does not claim the interface on linux systems
        try:
            self.devh.detachKernelDriver(self.iface)
        except (AttributeError, usb.USBError, NotImplementedError), e:
            logdbg("Detach failed: %s" % e)

        # attempt to claim the interface
        try:
            self.devh.claimInterface(0)
        except usb.USBError, e:
            self.close()
            msg = "Unable to claim USB interface %s: %s" % (self.iface, e)
            logerr(msg)
            raise weewx.WeeWxIOError(msg)

    def close(self):
        if self.devh:
            try:
                self.devh.releaseInterface()
            except (ValueError, usb.USBError), e:
                logerr("Release interface failed: %s" % e)
            self.devh = None

    def reset(self):
        # use a usb reset to restore communication with the device.
        # specific cases include when you do an interrupt write with bogus
        # data.  use a reset to bring the device back to responsiveness.
        for x in range(5):
            try:
                self.devh.reset()
                break
            except usb.USBError, e:
                logdbg("USB reset failed: %s" % e)
                time.sleep(2)

    def _write(self, buf, reqtype=None, req=None, wval=None, timeout=50):
        if reqtype is None:
            reqtype = usb.ENDPOINT_OUT | \
                usb.TYPE_CLASS | \
                usb.RECIP_INTERFACE
        if req is None:
            req = usb.REQ_SET_CONFIGURATION
        if wval is None:
            wval = 0x200
        return self.devh.controlMsg(
            reqtype,
            req,
            buf,
            value=wval,
            timeout=timeout)

    def _read(self, sz, timeout=1000, endpoint_in=usb.ENDPOINT_IN):
        return self.devh.interruptRead(endpoint_in, sz, timeout)

    @staticmethod
    def _find_dev(vendor_id, product_id):
        """Find the vendor and product ID on the USB."""
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == vendor_id and dev.idProduct == product_id:
                    return dev, bus.dirname, dev.filename
        return None, None, None

    @staticmethod
    def get_usb_info():
        pyusb_version = '0.4.x'
        try:
            pyusb_version = usb.__version__
        except AttributeError:
            pass
        return "pyusb_version=%s" % pyusb_version

    # these are usb 'errors' that are really not errors.
    USB_NONERROR_MESSAGES = [
        'No data available', 'No error',
        'Nessun dato disponibile', 'Nessun errore',
        'Keine Daten verf', # verfuegbar
        'No hay datos disponibles',
        'Pas de donn' # donnees disponibles
        ]

    def is_error(self, e):
        errmsg = repr(e)
        for msg in self.USB_NONERROR_MESSAGES:
            if msg in errmsg:
                return False
        return True
