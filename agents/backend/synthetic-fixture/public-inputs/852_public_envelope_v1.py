"""T44-852 neutral transport envelope v1.0.0; isolated cryptography dependency only.
This helper never imports HTTP measurement tools or sends network/application requests.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding,rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION='1.0.0'
FORMAT='T44-852-ENVELOPE-v1'
ALGORITHM='RSA-OAEP-SHA256-MGF1SHA256+A256GCM'
FIELDS={'protected','encrypted_key_b64','nonce_b64','ciphertext_and_tag_b64'}
PROTECTED={'format','algorithm','recipient_cert_sha256','purpose','content_type','created_utc'}


def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')


def strict_json(data):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('Invalid JSON constant')
    return json.loads(data,object_pairs_hook=pairs,parse_constant=invalid)


def b64(data):return base64.b64encode(data).decode('ascii')
def unb64(value):return base64.b64decode(value.encode('ascii'),validate=True)


def recipient(pem):
    cert=x509.load_pem_x509_certificate(pem)
    public=cert.public_key()
    if not isinstance(public,rsa.RSAPublicKey) or public.key_size<3072:
        raise ValueError('Recipient must be RSA with at least3072bits')
    return public,cert.fingerprint(hashes.SHA256()).hex()


def oaep():
    return padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None)


def encrypt(plaintext,certificate_pem,purpose,content_type='application/json'):
    if purpose not in ['neutral-environment','private-test-result','public-known-calibration']:
        raise ValueError('Unknown transport purpose')
    public,fingerprint=recipient(certificate_pem)
    protected={'format':FORMAT,'algorithm':ALGORITHM,'recipient_cert_sha256':fingerprint,
        'purpose':purpose,'content_type':content_type,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')}
    key=AESGCM.generate_key(bit_length=256)
    nonce=os.urandom(12)
    ciphertext=AESGCM(key).encrypt(nonce,plaintext,canonical(protected))
    return {'protected':protected,'encrypted_key_b64':b64(public.encrypt(key,oaep())),
            'nonce_b64':b64(nonce),'ciphertext_and_tag_b64':b64(ciphertext)}


def decrypt(envelope,certificate_pem,private_key_pem,expected_purpose):
    if set(envelope)!=FIELDS:raise ValueError('Unexpected envelope fields')
    protected=envelope['protected']
    if not isinstance(protected,dict) or set(protected)!=PROTECTED:raise ValueError('Unexpected protected fields')
    public,fingerprint=recipient(certificate_pem)
    if protected['format']!=FORMAT or protected['algorithm']!=ALGORITHM or protected['recipient_cert_sha256']!=fingerprint:
        raise ValueError('Envelope format/algorithm/recipient mismatch')
    if protected['purpose']!=expected_purpose:raise ValueError('Transport purpose mismatch')
    parsed=dt.datetime.fromisoformat(protected['created_utc'].replace('Z','+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset()!=dt.timedelta(0):raise ValueError('UTC timestamp required')
    private=serialization.load_pem_private_key(private_key_pem,password=None)
    if not isinstance(private,rsa.RSAPrivateKey) or private.public_key().public_numbers()!=public.public_numbers():
        raise ValueError('Private key does not match recipient certificate')
    wrapped=unb64(envelope['encrypted_key_b64'])
    nonce=unb64(envelope['nonce_b64'])
    ciphertext=unb64(envelope['ciphertext_and_tag_b64'])
    if len(wrapped)!=private.key_size//8 or len(nonce)!=12 or len(ciphertext)<16:
        raise ValueError('Invalid encrypted field length')
    key=private.decrypt(wrapped,oaep())
    if len(key)!=32:raise ValueError('Invalid AES key length')
    return AESGCM(key).decrypt(nonce,ciphertext,canonical(protected))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['encrypt','decrypt'])
    parser.add_argument('--certificate',required=True,type=Path)
    parser.add_argument('--private-key',type=Path)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--purpose',required=True)
    parser.add_argument('--content-type',default='application/json')
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Never overwrite an existing transport artifact')
    certificate=args.certificate.read_bytes()
    if args.operation=='encrypt':
        envelope=encrypt(args.input.read_bytes(),certificate,args.purpose,args.content_type)
        output=canonical(envelope)+b'\n'
    else:
        if args.private_key is None:raise ValueError('Private key required for decryption')
        envelope=strict_json(args.input.read_bytes())
        output=decrypt(envelope,certificate,args.private_key.read_bytes(),args.purpose)
    os.umask(0o077)
    with args.output.open('xb') as handle:handle.write(output)
    os.chmod(args.output,0o600)
    # No plaintext, secret key, credential, case or raw log is sent to stdout.
    result={'transport_version':VERSION,'operation':args.operation,'output_written':True,'application_requests':0}
    if args.operation=='encrypt':result['envelope_sha256']=hashlib.sha256(output).hexdigest()
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
