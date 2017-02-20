# Copyright (c) 2017 Tom Keffer <tkeffer@gmail.com>
# See the file LICENSE.txt for your rights.
"""USB utilities"""

import syslog
import weewx


def logmsg(level, msg):
    syslog.syslog(level, 'usbhid: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)


# Base class for USBHID implementations.  This provides the basic API as well
# as consistent error handling.
class USBHIDbase(object):
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, _, value, traceback):
        self.close()

    def open(self):
        raise NotImplemented()

    def close(self):
        raise NotImplemented()

    def reset(self):
        pass

    def flush(self):
        pass

    def _write(self, buf, reqtype, req, wval, timeout):
        raise NotImplemented()

    def _read(self, sz, timeout, endpoint_in):
        raise NotImplemented()

    def is_error(e):
        return True


# Try to load a USBHID implementation.
# linux - pyusb1 is preferred, but pyusb is ok too
# macos - prefer hidapi since libusb/pyusb have kernel attachment issues
modules = ['usbhid_ctypes_hidapi', 'usbhid_cython_hidapi',
           'usbhid_libusb1', 'usbhid_pyusb1', 'usbhid_pyusb']

for module_name in (modules):
    try:
        module = __import__(module_name, globals(), locals(), level=1)
        USBHID = getattr(module, 'USBHID')
        logdbg("usbhid: using %s" % module_name)
        break
    except ImportError:
        logdbg("usbhid: %s failed" % module_name)
else:
    raise ImportError("No USB library found")
