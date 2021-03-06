import zmq
import base64


class Timeout(Exception):
    """
    Raised when an operation times out
    """

context = zmq.Context()


def request(cmd, server="tcp://127.0.0.1:5555", timeout=3000):
    try:
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, timeout)
        socket.connect(server)
        socket.send(cmd)
        return socket.recv()
    except zmq.Again:
        raise Timeout()
    finally:
        socket.setsockopt(zmq.LINGER, 100)
        socket.close()


def add_cert(ruc, company_id, cert, key):
    return request("add_cert {} {} {} {}".format(ruc, company_id, base64.b64encode(cert), base64.b64encode(key)))


def del_cert(ruc, company_id):
    return request("del_cert {} {}".format(ruc, company_id))


def has_cert(ruc, company_id):
    res = request("has_cert {} {}".format(ruc, company_id))
    return res == 'true'


def sign(ruc, company_id, xml):
    res = request("sign {} {} {}".format(ruc, company_id, base64.b64encode(xml)))
    parts = res.split()
    if parts[0] == 'signed_xml':
        return base64.b64decode(parts[1])
