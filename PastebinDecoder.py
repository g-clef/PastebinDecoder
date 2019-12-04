import typing
import base64
import gzip
import magic


unicode_space = " ".encode('utf-8')


class PasteDecoder:

    @staticmethod
    def base64Encoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return base64.b64decode(file_data)
        except Exception:
            return None

    @staticmethod
    def base64ReverseEncoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return base64.b64decode(file_data[::-1])
        except Exception:
            return None

    @staticmethod
    def compressed(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return gzip.decompress(file_data)
        except Exception:
            return None

    @staticmethod
    def hexStringEncoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return bytes.fromhex(str(file_data))
        except Exception:
            return None

    @staticmethod
    def hexStringReverseEncoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return bytes.fromhex(str(file_data[::-1]))
        except Exception:
            return None

    @staticmethod
    def asciiStringEncoded(file_data: bytes) -> typing.Optional[bytes]:
        if unicode_space not in file_data:
            return None
        try:
            return ''.join([chr(int(ch)) for ch in file_data.split(" ".encode('utf-8'))]).encode("utf-8")
        except Exception:
            return None

    @staticmethod
    def asciiStringReverseEncoded(file_data: bytes) -> typing.Optional[bytes]:
        if unicode_space not in file_data:
            return None
        try:
            reversed_str = file_data.split(b" ")[::-1]
            return ''.join([chr(int(ch)) for ch in reversed_str]).encode('utf-8')
        except Exception:
            return None

    @staticmethod
    def binaryStringEncoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return "".join([chr(int(file_data[ch:ch+8], 2)) for ch in range(0, len(file_data), 8)]).encode('utf-8')
        except Exception:
            return None

    @staticmethod
    def binaryStringReverseEncoded(file_data: bytes) -> typing.Optional[bytes]:
        try:
            return "".join([chr(int(file_data[ch:ch+8], 2)) for ch in range(0, len(file_data), -8)]).encode('utf-8')
        except Exception:
            return None

    def text_decode(self, file_data) -> typing.Tuple[bytes, str]:
        decoded_file = self.base64Encoded(file_data)
        encoding = "base64"
        if decoded_file is None:
            decoded_file = self.base64ReverseEncoded(file_data)
            encoding = "base64Reversed"
        if decoded_file is None:
            decoded_file = self.hexStringEncoded(file_data)
            encoding = "hexString"
        if decoded_file is None:
            decoded_file = self.hexStringReverseEncoded(file_data)
            encoding = "hexStringReversed"
        if decoded_file is None:
            decoded_file = self.asciiStringEncoded(file_data)
            encoding = "asciiString"
        if decoded_file is None:
            decoded_file = self.asciiStringReverseEncoded(file_data)
            encoding = "asciiStringReversed"
        return decoded_file, encoding

    def handle(self, file_data: bytes) -> typing.Tuple[str, typing.List[bytes], str]:
        base_magic = magic.from_buffer(file_data, mime=True)
        # pure text things may be encoded. Try decoding them one of a number of ways, and then re-classifying
        encoding = list()
        if base_magic == "text/plain":
            # pure ascii text files may be anything, try decoding them multiple other ways.
            # round 1: try base64, hex encoding or binary encoding. (with possible reverses also)
            # round 2: try hex or binary encoding analysis on results of base64, since b64 can just be text.
            # round 3: check if the results are zip'd or gzip'd. If so, decompress results.
            decoded_file, first_round_encoding = self.text_decode(file_data)
            # tried all first-level decodes. If none of them worked, it's really text, and we're done.
            if decoded_file is None:
                return base_magic, [file_data, ], ""
            encoding.append(first_round_encoding)
            new_magic = magic.from_buffer(decoded_file, mime=True)
            # if the new magic is also text-like, re-try the above decoding
            if new_magic == 'text/plain':
                second_round_decode, second_round_encoding = self.text_decode(decoded_file)
                if second_round_decode is not None:
                    if second_round_encoding in ['base64', 'base64Reversed'] and \
                            first_round_encoding in ['base64', 'base64Reversed']:
                        # double-encoding of base64 is possible, but every instance of it that I've seen has been wrong.
                        return base_magic, [file_data], ""
                    decoded_file = second_round_decode
                    new_magic = magic.from_buffer(decoded_file, mime=True)
                    encoding.append(second_round_encoding)
            if new_magic == "application/gzip":
                uncompressed = self.compressed(decoded_file)
                if uncompressed is not None:
                    decoded_file = uncompressed
                    new_magic = magic.from_buffer(decoded_file, mime=True)
                    encoding.append("gzip")
            elif new_magic == "application/zip":
                # todo: handle decompresssing all the files in the zip and returning all of them.
                pass
            elif new_magic in ["data",
                               "image/jp2",
                               "application/octet-stream",
                               'application/x-empty',
                               "application/x-wine-extension-ini"] or \
                    new_magic.startswith("Non-ISO extended-ASCII") or \
                    new_magic.startswith("MPEG ADTS"):
                # data means that the decoding may have not exceptioned, but it's not recognizable as a file,
                # return the original in this case.
                # also, the jpeg2000 decoder is *full* of false positives
                #   so is the extended-ASCII decoder
                #   so is the mpeg decoder
                return base_magic, [file_data, ], ""

            return new_magic, [decoded_file, ], ",".join(encoding)
        elif base_magic in ['image/jp2', ] or base_magic.startswith("Non-ISO extended-ASCII"):
            # as mentioned above, there's a ton of false positives in some of these outputs.
            return "text/plain", [file_data, ], ""
        else:
            return base_magic, [file_data, ], ""
