import binascii, base64, json
from Crypto.Cipher import AES

aes_key = 'ghBiw75c83Qu3U4HS0KMrwRI06BJi17y'


# 兼容pycryptodome模块和pycrypto模块
class AESCipher(object):
    '''
    PyCrypto AES在Python 3.3中使用ECB模式实现。
     这使用非常基本的0x00填充，我会推荐PKCS5 / 7填充。
    '''

    def __init__(self, key):
        '''
        The constructor takes in a PLAINTEXT string as the key and converts it
        to a byte string to work with throughout the class.
        构造函数接受一个PLAINTEXT字符串作为键并将其转换
         到一个字节字符串在整个班级工作。
        '''
        # convert key to a plaintext byte string to work with it将密钥转换为明文字节字符串以使用它
        self.key = bytes(key, encoding='utf-8')
        self.BLOCK_SIZE = 16

    def pkcs7padding(self, data):
        bs = AES.block_size
        padding = bs - len(data) % bs
        padding_text = chr(padding) * padding
        return data + padding_text

    def pkcs7unpadding(self, data):
        data = str(data, encoding='utf8')
        lengt = len(data)
        unpadding = ord(data[lengt - 1])
        return data[0:lengt - unpadding]

    def __pad(self, raw):
        '''
        This right pads the raw text with 0x00 to force the text to be a
        multiple of 16.  This is how the CFX_ENCRYPT_AES tag does the padding.

        @param raw: String of clear text to pad
        @return: byte string of clear text with padding
        这右键填充0x00的原始文本强制文本是一个
         16的倍数。这是CFX_ENCRYPT_AES标签如何填充的。

         @param raw：清除文本的字符串
         @return：带填充的明文的字节串

        '''
        if (len(raw) % self.BLOCK_SIZE == 0):
            return raw
        padding_required = self.BLOCK_SIZE - (len(raw) % self.BLOCK_SIZE)
        padChar = b'\x00'
        data = raw.encode('utf-8') + padding_required * padChar
        return data

    def __unpad(self, s):
        '''
        This strips all of the 0x00 from the string passed in.

        @param s: the byte string to unpad
        @return: unpadded byte string
        这将从传入的字符串中去除所有的0x00。

         @参数s：要取消的字节字符串
         @return：unpadded字节字符串
        '''
        s = s.rstrip(b'\x00')
        return s

    def encrypt(self, raw):
        '''
        Takes in a string of clear text and encrypts it.

        @param raw: a string of clear text
        @return: a string of encrypted ciphertext
        输入一串明文并加密。

         @参数raw：一串明文
         @return：一串加密的密文
        '''
        if (raw is None) or (len(raw) == 0):
            raise ValueError('input text cannot be null or empty set')
        # padding put on before sent for encryption
        # raw = self.__pad(raw)
        raw = self.pkcs7padding(raw)
        try:
            cipher = AES.AESCipher(self.key[:32], AES.MODE_ECB)
            ciphertext = cipher.encrypt(raw)
        except Exception:
            cipher = AES.new(self.key[:32], AES.MODE_ECB)
            ciphertext = cipher.encrypt(bytes(raw, encoding="utf-8"))
        encrypted = base64.b64encode(ciphertext)
        return str(encrypted, encoding='utf8')
        # return encrypted

    def decrypt(self, enc):
        '''
        Takes in a string of ciphertext and decrypts it.

        @param enc: encrypted string of ciphertext
        @return: decrypted string of clear text
        '''
        if (enc is None) or (len(enc) == 0):
            raise ValueError('input text cannot be null or empty set')
        enc = base64.b64decode(enc)
        try:
            cipher = AES.AESCipher(self.key[:32], AES.MODE_ECB)
        except Exception:
            cipher = AES.new(self.key[:32], AES.MODE_ECB)
        enc = self.pkcs7unpadding(cipher.decrypt(enc))
        return enc


def en_pwd(ss):
    o = AESCipher(aes_key)
    b = o.encrypt(ss)
    return b


def de_pwd(ss):
    o = AESCipher(aes_key)
    return o.decrypt(ss)


if __name__ == "__main__":
    print(en_pwd("Password1@3456789"))
    print(de_pwd("zhzNL96p4EcXuHcY4G4+XA=="))
