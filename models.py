from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    google_id = ndb.StringProperty()


class Expense(ndb.Model):
    cost = ndb.FloatProperty()
    description = ndb.StringProperty()
    category = ndb.StringProperty()
    date = ndb.DateProperty(auto_now_add=True)
    comment = ndb.TextProperty()
    user = ndb.StringProperty()


class Category(ndb.Model):
    category = ndb.StringProperty()



