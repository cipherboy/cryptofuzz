#!/usr/bin/python3

from __future__ import print_function

import re

# Python2 <-> Python3 shim to make range behave like range on Python3
try:
    range = xrange
except NameError:
    pass

def ToCryptofuzzID(prefix, item):
    return 'fuzzing::datasource::ID("Cryptofuzz/{}/{}")'.format(prefix, item)

class ModeOfOperation(object):
    def __init__(self, cipher):
        self.modeDict = {}
        regexDict = {
                'CBC' : r'_?CBC',
                'CCM' : r'_?CCM',
                'CFB' : r'_?CFB[18]?',
                'CTR' : r'_?CTR',
                'ECB' : r'_?ECB',
                'GCM' : r'_?GCM',
                'OCB' : r'_?OCB',
                'OFB' : r'_?OFB',
                'XTS' : r'_?XTS',
        }

        for name, regex in regexDict.items():
            if bool(re.search(regex, cipher)):
                self.modeDict[name] = True

        if len(self.modeDict.keys()) > 1:
            print("Tried setting more than 1 mode, exiting")
            exit(1)

# Components
class Component(object):
    def __init__(self, name):
        self.name = name

class Module(Component):
    def __init__(self, module):
        super(Module, self).__init__(module)

class Operation(Component):
    def __init__(self, operation):
        super(Operation, self).__init__(operation)

class Cipher(Component):
    def __init__(self, cipher, isAEAD = False):
        super(Cipher, self).__init__(cipher)

        self.operation = ModeOfOperation(cipher)
        self.isAEAD = isAEAD
        self.isWRAP = bool(re.search(r'_WRAP', cipher))
        self.isAES = bool(re.search(r'^AES_', cipher))

class Digest(Component):
    def __init__(self, digest):
        super(Digest, self).__init__( digest)

# Tables
class Table(object):
    def __init__(self, prefix, tableDecl):
        self.table = []
        self.prefix = prefix
        self.tableDecl = ['uint64_t id', 'const char* name']
        self.tableDecl.extend(tableDecl)
    def checkDuplicates(self):
        # Sanity check to assert that no duplicate items are added
        nameList = [obj.name for obj in self.table]
        if len(set(nameList)) != len(nameList):
            print("Duplicate entry: {}, exiting".format(self.table[-1].name))
            exit(1)
    def Add(self, obj):
        self.table += [ obj ]
        self.checkDuplicates()
    def getStructName(self, asType):
        return "{}LUT{}".format(self.prefix, "_t" if asType else "")
    def GetTableDecl(self):
        outStr = ""
        outStr += "struct " + self.getStructName(True) + "{\n"
        for part in self.tableDecl:
            outStr += '    ' + part + ';\n'
        outStr += "};\n"
        return outStr
    def getTableEntryList(self):
        raise NotImplementedError()
    def ToCPPTable(self):
        outStr = ""
        outStr += "constexpr " + self.getStructName(True) + " " + self.getStructName(False) + "[] = {\n"
        for index in range(len(self.table)):
            outTableEntry = [ ToCryptofuzzID(self.prefix, self.table[index].name), "\"" + self.table[index].name + "\"" ]
            outTableEntry.extend( self.getTableEntryList(index) )

            if len(outTableEntry) != len(self.tableDecl):
                print("Size of table declaration and size of table entry doesn't match, exiting")
                exit(1)

            outStr += '    {' + ", ".join( outTableEntry ) + '},\n'

        outStr += '};\n\n'

        return outStr
    def ToCPPMap(self):
        outStr = ""
        outStr += "std::map<uint64_t, " + self.getStructName(True) + ">" + " " + self.getStructName(False) + "Map = {\n";
        for index in range(len(self.table)):
            outTableEntry = [ ToCryptofuzzID(self.prefix, self.table[index].name), "\"" + self.table[index].name + "\""]
            outTableEntry.extend( self.getTableEntryList(index) )

            if len(outTableEntry) != len(self.tableDecl):
                print("Size of table declaration and size of table entry doesn't match, exiting")
                exit(1)

            outStr += '    {' + outTableEntry[0] + ", {" + ", ".join( outTableEntry ) + '} },\n'

        outStr += '};\n\n'

        return outStr

class CipherTable(Table):
    def __init__(self):
        tableDecl = [
                "bool CBC",
                "bool CCM",
                "bool CFB",
                "bool CTR",
                "bool ECB",
                "bool GCM",
                "bool OCB",
                "bool OFB",
                "bool XTS",
                "bool AEAD",
                "bool WRAP",
                "bool AES",
        ]

        super(CipherTable, self).__init__('Cipher', tableDecl)
    def getTableEntryList(self, index):
        tableEntry = []

        tableEntry += [ 'true' if 'CBC' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'CCM' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'CFB' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'CTR' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'ECB' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'GCM' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'OCB' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'OFB' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if 'XTS' in self.table[index].operation.modeDict else 'false' ]
        tableEntry += [ 'true' if self.table[index].isAEAD else 'false' ]
        tableEntry += [ 'true' if self.table[index].isWRAP else 'false' ]
        tableEntry += [ 'true' if self.table[index].isAES else 'false' ]

        return tableEntry

class DigestTable(Table):
    def __init__(self):
        tableDecl = [
        ]

        super(DigestTable, self).__init__('Digest', tableDecl)
    def getTableEntryList(self, index):
        tableEntry = []
        
        return tableEntry

class ModuleTable(Table):
    def __init__(self):
        tableDecl = [
        ]

        super(ModuleTable, self).__init__('Module', tableDecl)
    def getTableEntryList(self, index):
        tableEntry = []

        return tableEntry

class OperationTable(Table):
    def __init__(self):
        tableDecl = [
        ]

        super(OperationTable, self).__init__('Operation', tableDecl)
    def getTableEntryList(self, index):
        tableEntry = []

        return tableEntry

modules = ModuleTable()
modules.Add( Module("Beast") )
modules.Add( Module("Botan") )
modules.Add( Module("CPPCrypto") )
modules.Add( Module("Crypto++") )
modules.Add( Module("EverCrypt") )
modules.Add( Module("Golang") )
modules.Add( Module("Monero") )
modules.Add( Module("Nettle") )
modules.Add( Module("OpenSSL") )
modules.Add( Module("Public Domain") )
modules.Add( Module("Reference implementations") )
modules.Add( Module("Veracrypt") )
modules.Add( Module("libgcrypt") )
modules.Add( Module("libsodium") )
modules.Add( Module("mbed TLS") )

operations = OperationTable()
operations.Add( Operation("Digest") )
operations.Add( Operation("HMAC") )
operations.Add( Operation("CMAC") )
operations.Add( Operation("SymmetricEncrypt") )
operations.Add( Operation("SymmetricDecrypt") )
operations.Add( Operation("KDF_SCRYPT") )
operations.Add( Operation("KDF_HKDF") )
operations.Add( Operation("KDF_TLS1_PRF") )
operations.Add( Operation("KDF_PBKDF1") )
operations.Add( Operation("KDF_PBKDF2") )
operations.Add( Operation("KDF_ARGON2") )
operations.Add( Operation("KDF_SSH") )

ciphers = CipherTable()

ciphers.Add( Cipher("AES") )
ciphers.Add( Cipher("AES_128_CBC") )
ciphers.Add( Cipher("AES_128_CBC_HMAC_SHA1") )
ciphers.Add( Cipher("AES_128_CBC_HMAC_SHA256") )
ciphers.Add( Cipher("AES_128_CCM") )
ciphers.Add( Cipher("AES_128_CFB") )
ciphers.Add( Cipher("AES_128_CFB1") )
ciphers.Add( Cipher("AES_128_CFB128") )
ciphers.Add( Cipher("AES_128_CFB8") )
ciphers.Add( Cipher("AES_128_CTR") )
ciphers.Add( Cipher("AES_128_ECB") )
ciphers.Add( Cipher("AES_128_OCB") )
ciphers.Add( Cipher("AES_128_OFB") )
ciphers.Add( Cipher("AES_128_WRAP") )
ciphers.Add( Cipher("AES_128_WRAP_PAD") )
ciphers.Add( Cipher("AES_128_XTS") )
ciphers.Add( Cipher("AES_192_CBC") )
ciphers.Add( Cipher("AES_192_CCM") )
ciphers.Add( Cipher("AES_192_CFB") )
ciphers.Add( Cipher("AES_192_CFB1") )
ciphers.Add( Cipher("AES_192_CFB128") )
ciphers.Add( Cipher("AES_192_CFB8") )
ciphers.Add( Cipher("AES_192_CTR") )
ciphers.Add( Cipher("AES_192_ECB") )
ciphers.Add( Cipher("AES_192_OFB") )
ciphers.Add( Cipher("AES_192_WRAP") )
ciphers.Add( Cipher("AES_192_WRAP_PAD") )
ciphers.Add( Cipher("AES_256_CBC") )
ciphers.Add( Cipher("AES_256_CBC_HMAC_SHA1") )
ciphers.Add( Cipher("AES_256_CCM") )
ciphers.Add( Cipher("AES_256_CFB") )
ciphers.Add( Cipher("AES_256_CFB1") )
ciphers.Add( Cipher("AES_256_CFB128") )
ciphers.Add( Cipher("AES_256_CFB8") )
ciphers.Add( Cipher("AES_256_CTR") )
ciphers.Add( Cipher("AES_256_ECB") )
ciphers.Add( Cipher("AES_256_OCB") )
ciphers.Add( Cipher("AES_256_OFB") )
ciphers.Add( Cipher("AES_256_WRAP") )
ciphers.Add( Cipher("AES_256_WRAP_PAD") )
ciphers.Add( Cipher("AES_256_XTS") )
ciphers.Add( Cipher("ARIA_128_CBC") )
ciphers.Add( Cipher("ARIA_128_CCM") )
ciphers.Add( Cipher("ARIA_128_CFB") )
ciphers.Add( Cipher("ARIA_128_CFB1") )
ciphers.Add( Cipher("ARIA_128_CFB128") )
ciphers.Add( Cipher("ARIA_128_CFB8") )
ciphers.Add( Cipher("ARIA_128_CTR") )
ciphers.Add( Cipher("ARIA_128_ECB") )
ciphers.Add( Cipher("ARIA_128_OFB") )
ciphers.Add( Cipher("ARIA_192_CBC") )
ciphers.Add( Cipher("ARIA_192_CCM") )
ciphers.Add( Cipher("ARIA_192_CFB") )
ciphers.Add( Cipher("ARIA_192_CFB1") )
ciphers.Add( Cipher("ARIA_192_CFB128") )
ciphers.Add( Cipher("ARIA_192_CFB8") )
ciphers.Add( Cipher("ARIA_192_CTR") )
ciphers.Add( Cipher("ARIA_192_ECB") )
ciphers.Add( Cipher("ARIA_192_OFB") )
ciphers.Add( Cipher("ARIA_256_CBC") )
ciphers.Add( Cipher("ARIA_256_CCM") )
ciphers.Add( Cipher("ARIA_256_CFB") )
ciphers.Add( Cipher("ARIA_256_CFB1") )
ciphers.Add( Cipher("ARIA_256_CFB128") )
ciphers.Add( Cipher("ARIA_256_CFB8") )
ciphers.Add( Cipher("ARIA_256_CTR") )
ciphers.Add( Cipher("ARIA_256_ECB") )
ciphers.Add( Cipher("ARIA_256_OFB") )
ciphers.Add( Cipher("BF_CBC") )
ciphers.Add( Cipher("BF_CFB") )
ciphers.Add( Cipher("BF_ECB") )
ciphers.Add( Cipher("BF_OFB") )
ciphers.Add( Cipher("BLOWFISH_CBC") )
ciphers.Add( Cipher("BLOWFISH_CFB64") )
ciphers.Add( Cipher("BLOWFISH_CTR") )
ciphers.Add( Cipher("BLOWFISH_ECB") )
ciphers.Add( Cipher("CAMELLIA_128_CBC") )
ciphers.Add( Cipher("CAMELLIA_128_CCM") )
ciphers.Add( Cipher("CAMELLIA_128_CFB") )
ciphers.Add( Cipher("CAMELLIA_128_CFB1") )
ciphers.Add( Cipher("CAMELLIA_128_CFB128") )
ciphers.Add( Cipher("CAMELLIA_128_CFB8") )
ciphers.Add( Cipher("CAMELLIA_128_CTR") )
ciphers.Add( Cipher("CAMELLIA_128_ECB") )
ciphers.Add( Cipher("CAMELLIA_128_GCM") )
ciphers.Add( Cipher("CAMELLIA_128_OFB") )
ciphers.Add( Cipher("CAMELLIA_192_CBC") )
ciphers.Add( Cipher("CAMELLIA_192_CCM") )
ciphers.Add( Cipher("CAMELLIA_192_CFB") )
ciphers.Add( Cipher("CAMELLIA_192_CFB1") )
ciphers.Add( Cipher("CAMELLIA_192_CFB128") )
ciphers.Add( Cipher("CAMELLIA_192_CFB8") )
ciphers.Add( Cipher("CAMELLIA_192_CTR") )
ciphers.Add( Cipher("CAMELLIA_192_ECB") )
ciphers.Add( Cipher("CAMELLIA_192_GCM") )
ciphers.Add( Cipher("CAMELLIA_192_OFB") )
ciphers.Add( Cipher("CAMELLIA_256_CBC") )
ciphers.Add( Cipher("CAMELLIA_256_CCM") )
ciphers.Add( Cipher("CAMELLIA_256_CFB") )
ciphers.Add( Cipher("CAMELLIA_256_CFB1") )
ciphers.Add( Cipher("CAMELLIA_256_CFB128") )
ciphers.Add( Cipher("CAMELLIA_256_CFB8") )
ciphers.Add( Cipher("CAMELLIA_256_CTR") )
ciphers.Add( Cipher("CAMELLIA_256_ECB") )
ciphers.Add( Cipher("CAMELLIA_256_GCM") )
ciphers.Add( Cipher("CAMELLIA_256_OFB") )
ciphers.Add( Cipher("CAST5_CBC") )
ciphers.Add( Cipher("CAST5_CFB") )
ciphers.Add( Cipher("CAST5_ECB") )
ciphers.Add( Cipher("CAST5_OFB") )
ciphers.Add( Cipher("CHACHA20") )
ciphers.Add( Cipher("DES") )
# DESX_A/DESX_B: See https://github.com/openssl/openssl/issues/9703#issuecomment-526197301
ciphers.Add( Cipher("DESX_A_CBC") )
ciphers.Add( Cipher("DESX_B_CBC") )
ciphers.Add( Cipher("DES_CBC") )
ciphers.Add( Cipher("DES_CFB") )
ciphers.Add( Cipher("DES_CFB1") )
ciphers.Add( Cipher("DES_CFB8") )
ciphers.Add( Cipher("DES_ECB") )
ciphers.Add( Cipher("DES_EDE") )
ciphers.Add( Cipher("DES_EDE3") )
ciphers.Add( Cipher("DES_EDE3_CBC") )
ciphers.Add( Cipher("DES_EDE3_CFB") )
ciphers.Add( Cipher("DES_EDE3_CFB1") )
ciphers.Add( Cipher("DES_EDE3_CFB8") )
ciphers.Add( Cipher("DES_EDE3_ECB") )
ciphers.Add( Cipher("DES_EDE3_OFB") )
ciphers.Add( Cipher("DES_EDE3_WRAP") )
ciphers.Add( Cipher("DES_EDE_CBC") )
ciphers.Add( Cipher("DES_EDE_CFB") )
ciphers.Add( Cipher("DES_EDE_ECB") )
ciphers.Add( Cipher("DES_EDE_OFB") )
ciphers.Add( Cipher("DES_OFB") )
ciphers.Add( Cipher("GOST-28147-89") )
ciphers.Add( Cipher("IDEA_CBC") )
ciphers.Add( Cipher("IDEA_CFB") )
ciphers.Add( Cipher("IDEA_ECB") )
ciphers.Add( Cipher("IDEA_OFB") )
ciphers.Add( Cipher("KALYNA128_CBC") )
ciphers.Add( Cipher("KALYNA128_CFB") )
ciphers.Add( Cipher("KALYNA128_CFB8") )
ciphers.Add( Cipher("KALYNA128_CTR") )
ciphers.Add( Cipher("KALYNA128_ECB") )
ciphers.Add( Cipher("KALYNA128_OFB") )
ciphers.Add( Cipher("KALYNA256_CBC") )
ciphers.Add( Cipher("KALYNA256_CFB") )
ciphers.Add( Cipher("KALYNA256_CFB8") )
ciphers.Add( Cipher("KALYNA256_CTR") )
ciphers.Add( Cipher("KALYNA256_ECB") )
ciphers.Add( Cipher("KALYNA256_OFB") )
ciphers.Add( Cipher("KALYNA512_CBC") )
ciphers.Add( Cipher("KALYNA512_CFB") )
ciphers.Add( Cipher("KALYNA512_CFB8") )
ciphers.Add( Cipher("KALYNA512_CTR") )
ciphers.Add( Cipher("KALYNA512_ECB") )
ciphers.Add( Cipher("KALYNA512_OFB") )
ciphers.Add( Cipher("KASUMI_CBC") )
ciphers.Add( Cipher("KASUMI_CTR") )
ciphers.Add( Cipher("KASUMI_OFB") )
ciphers.Add( Cipher("KASUMI_XTS") )
ciphers.Add( Cipher("KUZNYECHIK") )
ciphers.Add( Cipher("MISTY1_CBC") )
ciphers.Add( Cipher("MISTY1_CTR") )
ciphers.Add( Cipher("MISTY1_OFB") )
ciphers.Add( Cipher("MISTY1_XTS") )
ciphers.Add( Cipher("NOEKEON_CBC") )
ciphers.Add( Cipher("NOEKEON_CTR") )
ciphers.Add( Cipher("NOEKEON_OFB") )
ciphers.Add( Cipher("NOEKEON_XTS") )
ciphers.Add( Cipher("RC2_40_CBC") )
ciphers.Add( Cipher("RC2_64_CBC") )
ciphers.Add( Cipher("RC2_CBC") )
ciphers.Add( Cipher("RC2_CFB") )
ciphers.Add( Cipher("RC2_ECB") )
ciphers.Add( Cipher("RC2_OFB") )
ciphers.Add( Cipher("RC4") )
ciphers.Add( Cipher("RC4_40") )
ciphers.Add( Cipher("RC4_HMAC_MD5") )
ciphers.Add( Cipher("RC5_32_12_16_CBC") )
ciphers.Add( Cipher("RC5_32_12_16_CFB") )
ciphers.Add( Cipher("RC5_32_12_16_ECB") )
ciphers.Add( Cipher("RC5_32_12_16_OFB") )
ciphers.Add( Cipher("SEED_CBC") )
ciphers.Add( Cipher("SEED_CFB") )
ciphers.Add( Cipher("SEED_ECB") )
ciphers.Add( Cipher("SEED_OFB") )
ciphers.Add( Cipher("SERPENT") )
ciphers.Add( Cipher("SERPENT_CBC") )
ciphers.Add( Cipher("SERPENT_CTR") )
ciphers.Add( Cipher("SERPENT_OFB") )
ciphers.Add( Cipher("SERPENT_XTS") )
ciphers.Add( Cipher("SHACAL2_CBC") )
ciphers.Add( Cipher("SHACAL2_CTR") )
ciphers.Add( Cipher("SHACAL2_OFB") )
ciphers.Add( Cipher("SHACAL2_XTS") )
ciphers.Add( Cipher("SM4_CBC") )
ciphers.Add( Cipher("SM4_CFB") )
ciphers.Add( Cipher("SM4_CTR") )
ciphers.Add( Cipher("SM4_ECB") )
ciphers.Add( Cipher("SM4_OFB") )
ciphers.Add( Cipher("THREEFISH_512_CBC") )
ciphers.Add( Cipher("THREEFISH_512_CTR") )
ciphers.Add( Cipher("THREEFISH_512_OFB") )
ciphers.Add( Cipher("THREEFISH_512_XTS") )
ciphers.Add( Cipher("TWOFISH") )
ciphers.Add( Cipher("TWOFISH_CBC") )
ciphers.Add( Cipher("TWOFISH_CTR") )
ciphers.Add( Cipher("TWOFISH_OFB") )
ciphers.Add( Cipher("TWOFISH_XTS") )
ciphers.Add( Cipher("XTEA_CBC") )
ciphers.Add( Cipher("XTEA_CTR") )
ciphers.Add( Cipher("XTEA_OFB") )
ciphers.Add( Cipher("XTEA_XTS") )

# AEAD ciphers
ciphers.Add( Cipher("CHACHA20_POLY1305", True) )
ciphers.Add( Cipher("CHACHA20_POLY1305_LIBSODIUM", True) )
ciphers.Add( Cipher("XCHACHA20_POLY1305", True) )
ciphers.Add( Cipher("AES_128_GCM", True) )
ciphers.Add( Cipher("AES_128_GCM_SIV", True) )
ciphers.Add( Cipher("AES_128_GCM_TLS12", True) )
ciphers.Add( Cipher("AES_128_GCM_TLS13", True) )
ciphers.Add( Cipher("AES_192_GCM", True) )
ciphers.Add( Cipher("AES_256_GCM", True) )
ciphers.Add( Cipher("AES_256_GCM_SIV", True) )
ciphers.Add( Cipher("AES_256_GCM_TLS12", True) )
ciphers.Add( Cipher("AES_256_GCM_TLS13", True) )
ciphers.Add( Cipher("ARIA_128_GCM", True) )
ciphers.Add( Cipher("ARIA_192_GCM", True) )
ciphers.Add( Cipher("ARIA_256_GCM", True) )
ciphers.Add( Cipher("AES_256_CBC_HMAC_SHA256", True) )
ciphers.Add( Cipher("AES_128_CTR_HMAC_SHA256", True) )
ciphers.Add( Cipher("AES_256_CTR_HMAC_SHA256", True) )
ciphers.Add( Cipher("AES_128_CCM_BLUETOOTH", True) )
ciphers.Add( Cipher("AES_128_CCM_BLUETOOTH_8", True) )
ciphers.Add( Cipher("AES_128_CBC_SHA1_TLS", True) )
ciphers.Add( Cipher("AES_128_CBC_SHA1_TLS_IMPLICIT_IV", True) )
ciphers.Add( Cipher("AES_128_CBC_SHA256_TLS", True) )
ciphers.Add( Cipher("AES_256_CBC_SHA1_TLS", True) )
ciphers.Add( Cipher("AES_256_CBC_SHA1_TLS_IMPLICIT_IV", True) )
ciphers.Add( Cipher("AES_256_CBC_SHA256_TLS", True) )
ciphers.Add( Cipher("AES_256_CBC_SHA384_TLS", True) )
ciphers.Add( Cipher("DES_EDE3_CBC_SHA1_TLS", True) )
ciphers.Add( Cipher("DES_EDE3_CBC_SHA1_TLS_IMPLICIT_IV", True) )
ciphers.Add( Cipher("NULL_SHA1_TLS", True) )

digests = DigestTable()

digests.Add( Digest("ADLER32") )
digests.Add( Digest("BLAKE2B160") )
digests.Add( Digest("BLAKE2B256") )
digests.Add( Digest("BLAKE2B384") )
digests.Add( Digest("BLAKE2B512") )
digests.Add( Digest("BLAKE2S128") )
digests.Add( Digest("BLAKE2S160") )
digests.Add( Digest("BLAKE2S224") )
digests.Add( Digest("BLAKE2S256") )
digests.Add( Digest("CITYHASH32") )
digests.Add( Digest("CITYHASH64") )
digests.Add( Digest("CITYHASH128") )
digests.Add( Digest("CITYHASHCRC128") )
digests.Add( Digest("CITYHASHCRC256") )
digests.Add( Digest("CITYHASH64SEED8") )
digests.Add( Digest("CITYHASH64SEED16") )
digests.Add( Digest("CITYHASH128SEED16") )
digests.Add( Digest("CITYHASHCRC128SEED16") )
digests.Add( Digest("CRC32") )
digests.Add( Digest("CRC32-RFC1510") )
digests.Add( Digest("CRC32-RFC2440") )
digests.Add( Digest("GOST-28147-89") )
digests.Add( Digest("GOST-R-34.11-94") )
digests.Add( Digest("GOST-R-34.11-94-NO-CRYPTOPRO") )
digests.Add( Digest("GROESTL_224") )
digests.Add( Digest("GROESTL_256") )
digests.Add( Digest("GROESTL_384") )
digests.Add( Digest("GROESTL_512") )
digests.Add( Digest("JH_224") )
digests.Add( Digest("JH_256") )
digests.Add( Digest("JH_384") )
digests.Add( Digest("JH_512") )
digests.Add( Digest("KECCAK_224") )
digests.Add( Digest("KECCAK_256") )
digests.Add( Digest("KECCAK_384") )
digests.Add( Digest("KECCAK_512") )
digests.Add( Digest("MD2") )
digests.Add( Digest("MD4") )
digests.Add( Digest("MD5") )
digests.Add( Digest("MD5_SHA1") )
digests.Add( Digest("MDC2") )
digests.Add( Digest("PANAMA") )
digests.Add( Digest("RIPEMD128") )
digests.Add( Digest("RIPEMD160") )
digests.Add( Digest("RIPEMD256") )
digests.Add( Digest("RIPEMD320") )
digests.Add( Digest("SHA1") )
digests.Add( Digest("SHA224") )
digests.Add( Digest("SHA256") )
digests.Add( Digest("SHA3-224") )
digests.Add( Digest("SHA3-256") )
digests.Add( Digest("SHA3-384") )
digests.Add( Digest("SHA3-512") )
digests.Add( Digest("SHA384") )
digests.Add( Digest("SHA512") )
digests.Add( Digest("SHA512-224") )
digests.Add( Digest("SHA512-256") )
digests.Add( Digest("SHAKE128") )
digests.Add( Digest("SHAKE256") )
digests.Add( Digest("SKEIN_1024") )
digests.Add( Digest("SKEIN_256") )
digests.Add( Digest("SKEIN_512") )
digests.Add( Digest("SM3") )
digests.Add( Digest("STREEBOG-256") )
digests.Add( Digest("STREEBOG-512") )
digests.Add( Digest("T1HA-128") )
digests.Add( Digest("T1HA-64") )
digests.Add( Digest("TIGER") )
digests.Add( Digest("WHIRLPOOL") )
digests.Add( Digest("XXHASH32") )
digests.Add( Digest("XXHASH64") )

tables = [modules, operations, ciphers, digests]

with open('repository_tbl.h', 'w') as fp:
    for table in tables:
        fp.write(table.GetTableDecl())
        fp.write(table.ToCPPTable())
with open('repository_map.h', 'w') as fp:
    for table in tables:
        fp.write(table.GetTableDecl())
        fp.write(table.ToCPPMap())
