import tempfile
import os


def sign_data(xml_content, cert, key):
    d = tempfile.mkdtemp()
    try:
        cert_path = os.path.join(d, "cert")
        xml_path = os.path.join(d, "xml")
        with open(cert_path, "w") as f:
            f.write(cert)
        with open(xml_path, "w") as f:
            f.write(xml_content)
        os.system(
            'cd {signer_dir} && '
            'java'
            ' -classpath "core/*:deps/*:./sources/MITyCLibXADES/test/:."'
            ' XAdESBESSignature'
            ' {xml_path} {keystore_path} {keystore_pw}'
            ' {res_dir} xml_signed'.format(
                signer_dir='util/signer/',
                xml_path=xml_path,
                keystore_path=cert_path,
                keystore_pw=key,
                res_dir=d))
        with open(os.path.join(d, "xml_signed")) as f:
            return f.read()
    except IOError:
        # Failure to sign
        raise
    finally:
        for f in os.listdir(d):
            os.unlink(os.path.join(d, f))
        os.rmdir(d)
