import pyrebase


class PyrebaseInstance():

    def __init__(
        self,
        apiKey,
        authDomain,
        databaseURL,
        storageBucket,
    ):
        config = {
            "apiKey": apiKey,
            "authDomain": authDomain,
            "databaseURL": databaseURL,
            "storageBucket": storageBucket
        }
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()
