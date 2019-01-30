import binascii
import json

from Crypto import Random
from Crypto.Cipher import AES
from sqlalchemy import TypeDecorator, LargeBinary
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm.attributes import flag_modified


class InvalidEncryptionKey(Exception):
    pass


class FlaskEncryptedDict:
    def init_app(self, app):
        EncryptedDict.DB_ENCRYPTION_KEY = app.config.get("DB_ENCRYPTION_KEY")
        if not self.test_key():
            raise InvalidEncryptionKey("Encryption Key is invalid")

    @classmethod
    def change_key(cls, old_encryption_key, new_encryption_key):
        from ..extensions import db

        # This will iterate on all models registered in sqlalchemy
        # + _ModuleMarker
        for class_ in db.Model._decl_class_registry.values():
            # We ignore _ModuleMarker
            if isinstance(class_, _ModuleMarker):
                continue
            # We iterate through each instance and we use a noload to prevent
            # joins from reloading already reencrypted models
            for inst in class_.query.options(db.noload("*")).all():
                updated = False
                # We iterate through each columns of the instance's model
                for c in class_.__table__.columns:
                    # If the column is an EncryptedDict
                    if isinstance(c.type, EncryptedDict):
                        # We decrypt is value
                        setattr(inst, c.name, getattr(inst, c.name))
                        # We flag the column as modified in case the value was
                        # not encrypted so the commit still updates the column
                        flag_modified(inst, c.name)
                        updated = True
                if updated:
                    db.session.add(inst)
                    # We set the new encryption key just for the commit
                    EncryptedDict.DB_ENCRYPTION_KEY = new_encryption_key
                    # We encrypt the value with the new key
                    db.session.commit()
                    # We reset the key back to its original value
                    EncryptedDict.DB_ENCRYPTION_KEY = old_encryption_key

    @classmethod
    def generate_key(cls):
        """Generate a 256 bits key to be used to encrypt data.

        Return a string hex representation of this key.
        """
        try:
            return binascii.hexlify(Random.new().read(32)).decode()
        except AssertionError:
            Random.atfork()
            return cls.generate_key()

    def test_key(self):
        """Try to encrypt a simple text and check if we can get it back."""
        data = {"Hello": "hello"}
        es = EncryptedDict()
        try:
            edata = es.process_bind_param(data, None)
        except (binascii.Error, ValueError):
            return False
        return es.process_result_value(edata, None) == data


class EncryptedDict(TypeDecorator):
    """SQLAlchemy type for storing encrypted String.

    Strings are encrypted using AES CFB.
    The hex representation of the key is stored in Flask app config.
    Each new encryption generates a new random Initialization Vector.
    IV is prepended to the encrypted result data.
    """

    impl = LargeBinary
    DB_ENCRYPTION_KEY = None

    def process_bind_param(self, data, dialect):
        if data is not None:
            return self._aes_encrypt(json.dumps(data))

    def process_result_value(self, data, dialect):
        if data is not None:
            return json.loads(self._aes_decrypt(data))

    def _get_new_cipher(self, iv=None):
        if not iv:
            iv = EncryptedDict._generate_iv()
        key = binascii.unhexlify(self.DB_ENCRYPTION_KEY)
        return AES.new(key, AES.MODE_CFB, iv), iv

    def _aes_encrypt(self, data):
        """Encrypts data.

        Return an hex string containing 'IV + encrypted data'
        """
        data = data.encode("utf-8")
        if not self.DB_ENCRYPTION_KEY:
            return data
        cipher, iv = self._get_new_cipher()
        return_value = iv + cipher.encrypt(data)
        return return_value

    def _aes_decrypt(self, encrypted_hex_data_with_iv):
        """Decrypts data.

        Expects its parameter to be an hex string
        containing 'IV + encrypted data"
        """
        if not self.DB_ENCRYPTION_KEY:
            return encrypted_hex_data_with_iv.decode("utf-8")
        encrypted_data_with_iv = encrypted_hex_data_with_iv
        iv = encrypted_data_with_iv[0 : AES.block_size]
        encrypted_data = encrypted_data_with_iv[AES.block_size :]
        cipher, _ = self._get_new_cipher(iv=iv)
        return_value = cipher.decrypt(encrypted_data)
        return return_value.decode("utf-8")

    @classmethod
    def _generate_iv(cls):
        try:
            return Random.new().read(AES.block_size)
        except AssertionError:
            Random.atfork()
            return cls._generate_iv()
