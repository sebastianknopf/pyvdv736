import logging
import os
import platform
import sqlite3
import tempfile

from .model import PublicTransportSituation
from .model import Subscription


class LocalNodeDatabase:

    def __init__(self, name):
        # create logger
        self._logger = logging.getLogger('uvicorn')

        # connect to database
        tempdir = "/tmp" if platform.system() == "Darwin" else tempfile.gettempdir()
        self._filename = os.path.join(tempdir, name)

        self._connection = sqlite3.connect(self._filename, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row

        # init required tables if not already done
        cursor = self._connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS subscriptions (id TEXT NOT NULL PRIMARY KEY, serialized TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS situations (id TEXT NOT NULL PRIMARY KEY, serialized TEXT NOT NULL)")
        self._connection.commit()

    def get_subscriptions(self) -> dict[str, Subscription]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM subscriptions")

        subscriptions = dict()
        for s in cursor.fetchall():
            subscription = Subscription.unserialize(s['serialized'])
            subscriptions[s['id']] = subscription

        return subscriptions

    def add_subscription(self, subscription_id: str, subscription: Subscription) -> bool:
        try:
            serialized = Subscription.serialize(subscription)
            
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO subscriptions (id, serialized) VALUES (?, ?)", (
                subscription_id,
                serialized,
            ))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False
        
    def update_subscription(self, subscription_id: str, subscription: Subscription) -> bool:
        try:
            serialized = Subscription.serialize(subscription)
            
            cursor = self._connection.cursor()
            cursor.execute("UPDATE subscriptions SET serialized = ? WHERE id = ?", (
                serialized, 
                subscription_id
            ))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False

    def remove_subscription(self, subscription_id: str) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM subscriptions WHERE id = ?", (subscription_id,))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False

    def get_situations(self) -> dict[str, PublicTransportSituation]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM situations")

        subscriptions = dict()
        for s in cursor.fetchall():
            situation = PublicTransportSituation.unserialize(s['serialized'])
            subscriptions[s['id']] = situation

        return subscriptions
    
    def add_situation(self, situation_id, situation: PublicTransportSituation) -> bool:
        try:
            serialized = PublicTransportSituation.serialize(situation)
            
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO situations (id, serialized) VALUES (?, ?)", (
                situation_id,
                serialized,
            ))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False
        
    def update_situation(self, situation_id, situation: PublicTransportSituation) -> bool:
        try:
            serialized = PublicTransportSituation.serialize(situation)
            
            cursor = self._connection.cursor()
            cursor.execute("UPDATE situations SET serialized = ? WHERE id = ?", (
                serialized, 
                situation_id,
            ))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False
        
    def add_or_update_situation(self, situation_id, situation: PublicTransportSituation) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT COUNT(*) AS 'count' FROM situations WHERE id = ?", (situation_id,))
            count = cursor.fetchone()['count']

            if count == 0:
                self.add_situation(situation_id, situation)
            else:
                self.update_situation(situation_id, situation)

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False

    def remove_situation(self, situation_id) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM situations WHERE id = ?", (situation_id,))
            self._connection.commit()

            return True
        except sqlite3.Error as ex:
            self._logger.error(ex)
            return False
        
    def close(self, remove=False) -> None:
        self._connection.close()

        if remove == True:
            try:
                os.remove(self._filename)
            except PermissionError as ex:
                self._logger.error(ex)


def local_node_database(name: str) -> LocalNodeDatabase:
    if not name.endswith('.db3'):
        name = name + '.db3'

    return LocalNodeDatabase(name)