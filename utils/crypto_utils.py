# -*- coding: utf-8 -*-
'''封裝了常用的加密、hash等'''

import hashlib, uuid, os, sys
from typing import Union, Literal

try:
    import crypto
    sys.modules['Crypto'] = crypto
except ImportError:
    import Crypto as crypto
    sys.modules['crypto'] = crypto
from crypto.Cipher import AES
try:
    from crypto.Util.Padding import pad as _pad, unpad as _unpad
except ImportError:
    from crypto.Util.py3compat import bchr, bord
    def _pad(data_to_pad, block_size):
        padding_len = block_size - len(data_to_pad) % block_size
        padding = bchr(padding_len) * padding_len
        return data_to_pad + padding
    def _unpad(padded_data, block_size):
        pdata_len = len(padded_data)
        if pdata_len % block_size:
            raise ValueError("Input data is not padded")
        padding_len = bord(padded_data[-1])
        if padding_len < 1 or padding_len > min(block_size, pdata_len):
            raise ValueError("Padding is incorrect.")
        if padded_data[-padding_len:] != bchr(padding_len) * padding_len:
            raise ValueError("PKCS#7 padding is incorrect.")
        return padded_data[:-padding_len]

#region AES
def encrypt_file(key, in_filePath:str, outPath=None, deleteOriginFile=False, chunksize=64*1024) -> str:
    '''return encrypted file path'''
    in_filename = os.path.basename(in_filePath)
    out_filename = in_filename + '.enc'
    if outPath:
        out_filePath = os.path.join(outPath, out_filename)
    else:
        out_filePath = os.path.join(os.path.dirname(in_filePath), out_filename)
    iv = os.urandom(16)
    hashKey = getMD5Hash_fromString(key, 'bytes')
    encryptor = AES.new(hashKey, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)
    with open(in_filePath, 'rb') as infile:
        with open(out_filePath, 'wb') as outfile:
            outfile.write(iv)
            pos = 0
            while pos < filesize:
                chunk = infile.read(chunksize)
                pos += len(chunk)
                if pos == filesize:
                    chunk = _pad(chunk, AES.block_size)
                outfile.write(encryptor.encrypt(chunk))
            #print("Encrypted file: " + in_filename + " to " + out_filename)
    if deleteOriginFile:
        os.remove(in_filePath)
        #print("Deleted origin file: " + in_filePath)
    return out_filePath
def decrypt_file(key:str, in_filePath:str, out_filename=None, outPath=None, chunksize=64*1024) -> str:
    '''Chunck size default=64*1024. Return decrypted file path'''
    in_filename = os.path.basename(in_filePath)
    if not out_filename:
        out_filename = in_filename + '.dec'
    if outPath:
        out_filePath = os.path.join(outPath, out_filename)
    else:
        out_filePath = os.path.join(os.path.dirname(in_filePath), out_filename)
    with open(in_filename, 'rb') as infile:
        iv = infile.read(16)
        hashKey = getMD5Hash_fromString(key,'bytes')
        encryptor = AES.new(hashKey, AES.MODE_CBC, iv)
        with open(out_filePath, 'wb') as outfile:
            encrypted_filesize = os.path.getsize(in_filename)
            pos = 16 # the IV.
            while pos < encrypted_filesize:
                chunk = infile.read(chunksize)
                pos += len(chunk)
                chunk = encryptor.decrypt(chunk)
                if pos == encrypted_filesize:
                    chunk = _unpad(chunk, AES.block_size)
                outfile.write(chunk)
            #print("Decrypted file: " + in_filename + " to " + out_filename)
    return out_filePath
#endregion

#region MD5
def getMD5Hash_fromFile(filePath, mode:Literal['hex', 'bytes']='hex'):
    '''return 32 hex string or 16 bytes'''
    h = hashlib.md5()
    with open(filePath, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            h.update(data)
    return h.hexdigest() if mode == 'hex' else h.digest()
def getMD5Hash_fromString(string, mode:Literal['hex', 'bytes']='hex'):
    '''return 32 hex string or 16 bytes'''
    return hashlib.md5(string.encode('utf-8')).hexdigest() if mode == 'hex' else hashlib.md5(string.encode('utf-8')).digest()
def getMD5Hash_fromBytes(bytes, mode:Literal['hex', 'bytes']='hex'):
    '''return 32 hex string or 16 bytes'''
    return hashlib.md5(bytes).hexdigest() if mode == 'hex' else hashlib.md5(bytes).digest()
def checkMD5Hash_fromFile(filePath, hash):
    '''check if file's md5 hash is equal to hash'''
    return hash == getMD5Hash_fromFile(filePath)
def checkMD5Hash_fromString( string, hash):
    '''check if string's md5 hash is equal to hash'''
    return hash == getMD5Hash_fromString(string)
def checkMD5Hash_fromBytes( bytes, hash):
    '''check if bytes's md5 hash is equal to hash'''
    return hash == getMD5Hash_fromBytes(bytes)
def checkFileSame_byMD5Hash(file1:Union[str, 'FileInfo'], file2:Union[str, 'FileInfo']):
    '''check if two files are same by md5 hash'''
    filePath1 = file1 if isinstance(file1, str) else file1.filePath
    filePath2 = file2 if isinstance(file2, str) else file2.filePath
    return getMD5Hash_fromFile(filePath1) == getMD5Hash_fromFile(filePath2)
#endregion

#region SHA256
def getSHA256Hash_fromFile(filePath, mode:Literal['hex', 'bytes']='hex'):
    '''return 64 hex string or 32 bytes'''
    h = hashlib.sha256()
    with open(filePath, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            h.update(data)
    return h.hexdigest() if mode == 'hex' else h.digest()
def getSHA256Hash_fromString(string, mode:Literal['hex', 'bytes']='hex'):
    '''return 64 hex string or 32 bytes'''
    return hashlib.sha256(string.encode('utf-8')).hexdigest() if mode == 'hex' else hashlib.sha256(string.encode('utf-8')).digest()
def getSHA256Hash_fromBytes(bytes, mode:Literal['hex', 'bytes']='hex'):
    '''return 64 hex string or 32 bytes'''
    return hashlib.sha256(bytes).hexdigest() if mode == 'hex' else hashlib.sha256(bytes).digest()
def checkSHA256Hash_fromFile(filePath, hash):
    '''return 64 hex string or 32 bytes'''
    return hash == getSHA256Hash_fromFile(filePath)
def checkSHA256Hash_fromString(string, hash):
    '''check hash from string'''
    return hash == getSHA256Hash_fromString(string)
def checkSHA256Hash_fromBytes(bytes, hash):
    '''check hash from bytes'''
    return hash == getSHA256Hash_fromBytes(bytes)
def checkFileSame_bySHA256Hash(file1:Union[str, 'FileInfo'], file2:Union[str, 'FileInfo']):
    '''check file equality with hash'''
    filePath1 = file1 if isinstance(file1, str) else file1.filePath
    filePath2 = file2 if isinstance(file2, str) else file2.filePath
    return getSHA256Hash_fromFile(filePath1) == getSHA256Hash_fromFile(filePath2)
#endregion

def generateUUID():
    '''return len 32 random ID'''
    return str((uuid.uuid5(uuid.NAMESPACE_DNS, str(uuid.uuid1()) + str(os.urandom(16))))).replace('-', '')

__all__ = ['getMD5Hash_fromFile', 'getMD5Hash_fromString', 'checkMD5Hash_fromFile', 'checkMD5Hash_fromString', 'checkFileSame_byMD5Hash', 'getSHA256Hash_fromFile',
           'getSHA256Hash_fromString', 'checkSHA256Hash_fromFile', 'checkSHA256Hash_fromString', 'checkFileSame_bySHA256Hash',
           'generateUUID', 'encrypt_file', 'decrypt_file', 'getMD5Hash_fromBytes', 'getSHA256Hash_fromBytes', 'checkMD5Hash_fromBytes',
              'checkSHA256Hash_fromBytes']