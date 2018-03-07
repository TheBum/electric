# Requires the MFRC522.py Python module available here:
#    https://github.com/pimylifeup/MFRC522-python

import datetime
import threading
import time
import logging
import copy
import MFRC522
from Queue import Queue
import RPi.GPIO as GPIO

logger = logging.getLogger('electric.worker.statusthread')
lone_read_thread = None
lone_write_thread = None

class TagIO:
    RCT_TAG  = 0x08     # MIFARE 1K
    REVO_TAG = 0x00     # MIFARE UL
    AUTH_KEY = (0xFF,0xFF,0xFF,0xFF,0xFF,0xFF)

    RCT_SCHEMA = { 60: { "battery id"    :( 0, 2 ),   \
                         "capacity"      :( 2, 2 ),   \
                         "cycle count"   :( 4, 2 ),   \
                         "cell count"    :( 6, 2 ) }, \
                   61: { "c rating"      :( 0, 2 ) }, \
                   62: { "chemistry"     :( 0, 2 ),   \
                         "max charge c"  :( 2, 2 ),   \
                         "charge rate"   :( 4, 4 ),   \
                         "discharge rate":( 8, 4 ) } }
    REVO_SCHEMA = {}

    def __init__(self):
        self.read_writer = MFRC522.MFRC522()
        self.tag_uid = None
        self.last_trailer_block = None

    def detect_tag(self):
        time.sleep(0.5)
        (status,req_type) = \
                  self.read_writer.MFRC522_Request(self.read_writer.PICC_REQIDL)
        if status == self.read_writer.MI_OK:
            (status,self.tag_uid) = self.read_writer.MFRC522_Anticoll()
            logger.info("detect_tag: (status,self.tag_uid) = (", status, ",", \
                        self.tag_uid, ")")
            if status == self.read_writer.MI_OK:
                type = self.read_writer.MFRC522_SelectTag(self.tag_uid)
                if type == self.REVO_TAG or type == self.RCT_TAG:
                    return (type,self.tag_uid)
        return (None, None)

    @classmethod
    def get_schema(cls, type):  # Provide a copy so it doesn't get corrupted
        if type == cls.RCT_TAG:
            return (copy.deepcopy(cls.RCT_SCHEMA), True)    # Writable = True
        elif type == cls.REVO_TAG:
            return (copy.deepcopy(cls.REVO_SCHEMA), False)  # Writable = False
        else:
            return (None, None)

    def read_block(self, block):
        print "tag_uid = ", self.tag_uid
        print "block = ", block
        trailer_block = block // 4 * 4 + 3
        print "trailer_block =",trailer_block,"last =",self.last_trailer_block
        if trailer_block != self.last_trailer_block:
            self.read_writer.MFRC522_StopCrypto1()
            status = self.read_writer.MFRC522_Auth( \
                                      self.read_writer.PICC_AUTHENT1A, \
                                      block, self.AUTH_KEY, self.tag_uid)
            print "After read Auth: AUTH_KEY =", self.AUTH_KEY
            if status != self.read_writer.MI_OK:
                return None
            else:
                self.last_trailer_block = trailer_block
        data = self.read_writer.MFRC522_Read(block)
        print "block[",block,"] = ",data
        return data

    def write_block(self, block, data):
        print "tag_uid = ", self.tag_uid
        print "block = ", block
        trailer_block = block // 4 * 4 + 3
        "trailer_block =",trailer_block,"last =",self.last_trailer_block
        if trailer_block != self.last_trailer_block:
            self.read_writer.MFRC522_StopCrypto1()
            status = self.read_writer.MFRC522_Auth(self.read_writer.PICC_AUTHENT1A, \
                                                  block, \
                                                  self.AUTH_KEY, self.tag_uid)
            print "After write Auth: AUTH_KEY =", self.AUTH_KEY
            if status != self.read_writer.MI_OK:
                return None
            else:
                self.last_trailer_block = trailer_block
                status = self.read_writer.MFRC522_Read(trailer_block)
                if status != cls.read_writer.MI_OK:
                    return None
        print "write block, data = ", block, ",",data
        self.read_writer.MFRC522_Write(block, data)
        data = self.read_writer.MFRC522_Read(block)
        print "read back block, data = ", block, ",",data
        return data

    def read_tag(self, schema):
        batt_info = {}

        for block in schema.keys():
            print "block in schema.keys =", block
            data = self.read_block(block)
            print "data in block =", data
            if data == None:
                return None
            block_dict = schema[block]

            for param in block_dict.keys():
                posn_tuple = block_dict[param]
                start_byte = posn_tuple[0]
                byte_len = posn_tuple[1]

                if byte_len == 1:
                    batt_info[param] = data[start_byte]
                elif byte_len == 2:
                    batt_info[param] = (data[start_byte]     << 8) | \
                                        data[start_byte + 1]
                elif byte_len == 3:
                    batt_info[param] = (data[start_byte]     << 16) | \
                                       (data[start_byte + 1] <<  8) | \
                                        data[start_byte + 2]
                elif byte_len == 4:
                    batt_info[param] = (data[start_byte]     << 24) | \
                                       (data[start_byte + 1] << 16) | \
                                       (data[start_byte + 2] <<  8) | \
                                        data[start_byte + 3]

        return batt_info

    def write_tag(self, schema, batt_info):
        for block in schema.keys():
            data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            block_dict = schema[block]
            print "batt_info = ", batt_info

            for param in block_dict.keys():
                posn_tuple = block_dict[param]
                print "posn_tuple = ", posn_tuple
                start_byte = posn_tuple[0]
                print "start_byte = ", start_byte
                byte_len = posn_tuple[1]
                print "byte_len = ", byte_len
                value = batt_info[param]
                print "value = ", value

                if byte_len == 1:
                    data[start_byte] = value & 0xFF
                elif byte_len == 2:
                    data[start_byte]     = value >> 8
                    data[start_byte + 1] = value & 0xFF
                elif byte_len == 3:
                    data[start_byte]     = value >> 16
                    data[start_byte + 1] = (value >> 8) & 0xFF
                    data[start_byte + 2] = value & 0xFF
                elif byte_len == 4:
                    data[start_byte]     = value >> 24
                    data[start_byte + 1] = (value >> 16) & 0xFF
                    data[start_byte + 2] = (value >> 8) & 0xFF
                    data[start_byte + 3] = value & 0xFF
                print "block =", block, "data =",data

            # Don't write the block if nothing changed
            print "Data after conversion from batt_info =", data
            current_data = self.read_block(block)
            print "Data currently in target block =", current_data
            if current_data != data:
                print "New data to write!"
                if self.write_block(block, data) == None:
                    return None

        print "data = ", data
        return self.read_tag(schema)

    def reset(self):
        self.read_writer.MFRC522_Init()
        self.last_trailer_block = None

class TagReader(threading.Thread):
    def __init__(self):
        super(TagReader, self).__init__(name="Read RFID tags")
        self.loop_done = False
        self.battery_data = { "chemistry":None, "cell count":None, \
                              "charge rate":0, "discharge rate":0, \
                              "battery ids":[] }

    def run(self):
        prev_uid = None
        tio = TagIO()
        while not self.loop_done:
            tio.reset()
            (type, uid) = tio.detect_tag()
            if uid == None or uid == prev_uid:
                continue
            prev_uid = uid

            (schema, writable) = tio.get_schema(type)
            if schema != None:
                batt_info = tio.read_tag(schema)
                print "post-read batt_info = ", batt_info
                if batt_info != None and writable:
                    # Increment cycle count if needed
                    print "post-read batt_info = ", batt_info
                    if False:# If the battery has been cycled since the last bump:
                        batt_info["cycle count"] += 1
                        new_batt_info = tio.write_tag(schema, batt_info)
                        if new_batt_info != None:
                            batt_info = new_batt_info
                            # Reset the "cycled" flag for this battery
            else:
                print "Invalid tag type: ", type
                continue

            print "preregister_batt_info = ", batt_info
            if (batt_info["battery id"], uid) \
                                       not in self.battery_data["battery ids"]:
                if self.battery_data["battery ids"] == []:
                    self.battery_data["chemistry"] = batt_info["chemistry"]
                    self.battery_data["cell count"] = batt_info["cell count"]
                elif self.battery_data["chemistry"] != batt_info["chemistry"] or\
                     self.battery_data["cell count"] != batt_info["cell count"]:
                    continue
                self.battery_data["charge rate"] += batt_info["charge rate"]
                self.battery_data["discharge rate"] += batt_info["discharge rate"]
                self.battery_data["battery ids"].append((batt_info["battery id"], uid))

class TagWriter(threading.Thread):
    SUCCESS = 0
    IN_PROGRESS = 1
    FAILED = 2
    USED_TAG = 3
    READONLY_TAG = 4
    INVALID_TAG = 5

    def __init__(self, batt_info, **kwargs):
        super(TagWriter, self).__init__(name="Write RFID tag")
        self.loop_done = False
        self.write_result = None
        self.batt_info = batt_info
        self.force = kwargs.get("force", False)

    def run(self):
        self.write_result = self.IN_PROGRESS
        tio = TagIO()
        while not self.loop_done:
            tio.reset()
            (type, uid) = tio.detect_tag()
            if uid == None:
                continue

            (schema, writable) = tio.get_schema(type)
            if schema != None:
                if not writable:
                    self.write_result = self.READONLY_TAG
                    break
                if not self.force:
                    batt_info = tio.read_tag(schema)
                    print "batt_info during virginity check =", batt_info
                    # Capacity should be 0 on a virgin tag
                    if batt_info["capacity"] != 0:
                        # Tag already written; must use force to overwrite
                        self.write_result = self.USED_TAG
                        break
            else:
                self.write_result = self.INVALID_TAG
                break

            if tio.write_tag(schema, self.batt_info) == None:
                self.write_result = self.FAILED
            else:
                self.write_result = self.SUCCESS
            break

def start_tag_reader():
    global lone_read_thread

    if lone_read_thread != None:
        stop_tag_reader()
    lone_read_thread = TagReader()
    lone_read_thread.start()
    logger.info("start_tag_reading: thread started")
    return lone_read_thread

def stop_tag_reader():
    global lone_read_thread

    if lone_read_thread != None:
        lone_read_thread.loop_done = True
        lone_read_thread.join()
        lone_read_thread = None

def start_tag_writer(parameters, **kwargs):
    global lone_write_thread

    if lone_write_thread != None:
        abort_tag_writer()
    lone_write_thread = TagWriter(parameters, **kwargs)
    lone_write_thread.start()
    return lone_write_thread

def abort_tag_writer():
    global lone_write_thread

    if lone_write_thread != None:
        lone_write_thread.loop_done = True
        lone_write_thread.join()
        lone_write_thread = None

def get_tag_write_result():
    global lone_write_thread

    if lone_write_thread != None:
        return lone_write_thread.write_result
    else:
        return None

def get_tag_read_data():
    global lone_read_thread

    if lone_read_thread != None:
        return lone_read_thread.battery_data
    else:
        return None
