import locale
import sys

from rs.helper.logger import log, log_to_run


def _decode_response_line(raw_response: bytes) -> str:
    encodings = ["utf-8", locale.getpreferredencoding(False), sys.stdin.encoding, "gbk"]
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return raw_response.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_response.decode("utf-8", errors="replace")


class Client:

    def __init__(self):
        self.send_message("ready")

    def send_message(self, message: str, silent: bool = False, before_run: bool = False) -> str:
        if not silent:
            log_message = f"Sending message: {message}"
            if before_run:
                log(log_message)
            else:
                log_to_run(log_message)
        sys.stdout.buffer.write((message + "\n").encode('utf-8'))
        sys.stdout.buffer.flush()
        input_response = _decode_response_line(sys.stdin.buffer.readline()).rstrip('\r\n')
        if not silent:
            log_message = f"Response: {input_response}"
            if before_run:
                log(log_message)
            else:
                log_to_run(log_message)
        return input_response
