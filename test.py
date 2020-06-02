#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import KeyStore
from config import Config
from app.main import bp
import os


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class UserModelCase(unittest.TestCase):
    key="test"
    insvalue="test123"
    insertime = datetime.utcnow()

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        if hasattr(self, '_outcome'):  # Python 3.4+
            result = self.defaultTestResult()  # these 2 methods have no side effects
            self._feedErrorsToResult(result, self._outcome.errors)
        else:  # Python 3.2 - 3.3 or 2.7
            result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        # demo: report short info immediately (not important)
        if not ok:
            typ, text = ('ERROR', error) if error else ('FAIL', failure)
            msg = [x for x in text.split('\n')[1:] if not x.startswith(' ')][0]
            msg2="\n== tearDown check: %s: %s\n     %s" % (typ, self.id(), msg)
            print(msg2)
            f = open("error.txt", "w")
            f.write(msg2)
            f.close()

        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    def test_database_insert(self):        
        temp = KeyStore(timestamp=self.insertime, key=self.key, value=self.insvalue)
        db.session.add(temp)
        db.session.commit()

        #Check if Value is in DB
        tempkey = KeyStore.query.filter_by(key=self.key).first()
        self.assertEquals(tempkey.value,self.insvalue)

    def test_database_remove(self):
        
        tempkey = KeyStore.query.filter_by(key=self.key).first()
        if tempkey is not None:
            db.session.delete(tempkey)
            db.session.commit()

        tempkey = KeyStore.query.filter_by(key=self.key).first()
        self.assertEquals(tempkey,None)   
 
if __name__ == '__main__':
    unittest.main(verbosity=2)