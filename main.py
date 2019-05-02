import os
import jinja2
import webapp2
from google.appengine.api import users
from models import User
from models import Expense
from models import Category
import datetime

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if params is None:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            registered_user_list = User.query(User.google_id == user.user_id()).fetch(1)
            if len(registered_user_list) == 0:
                registrated_user = User(name=user.nickname(), email=user.email(), google_id=user.user_id())
                registrated_user.put()
            else:
                registrated_user = registered_user_list[0]
            params = {"logged_in": logged_in, "logout_url": logout_url, "user": user, "registrated_user": registrated_user}
        else:
            logged_in = False
            login_url = users.create_login_url('/')
            params = {"logged_in": logged_in, "login_url": login_url, "user": user}
        return self.render_template("index.html", params)


def not_logged_in():
    google_user = users.get_current_user()
    if google_user is None:
        return True


class AddExpenseHandler(BaseHandler):
    def get(self):
        if not_logged_in():
            return webapp2.redirect('/')
        categories = Category.query().fetch()
        return self.render_template("add_expense.html", {"categories": categories})


class ResultHandler(BaseHandler):
    def post(self):
        user = users.get_current_user()
        current_user = User.query(User.google_id == user.user_id()).fetch(1)[0]
        expense_user = current_user.google_id
        description = self.request.get("description")
        expense = float(self.request.get("expense"))
        category = self.request.get("category")
        str_date = self.request.get("date")
        year, month, day = map(int, str_date.split('-'))
        date = datetime.date(year, month, day)
        comment = self.request.get("comment")
        new_expense = Expense(description=description, cost=expense,
                              category=category, comment=comment, date=date, user=expense_user)
        new_expense.put()
        return self.render_template("result.html", {"new_expense": new_expense})


class EditExpenseHandler(BaseHandler):
    def get(self, expense_id):
        expense = Expense.get_by_id(int(expense_id))
        categories = Category.query().fetch()
        return self.render_template("edit_expense.html", {"expense": expense, "categories": categories})

    def post(self, expense_id):
        new_description = self.request.get("description")
        new_cost = float(self.request.get("cost"))
        category = self.request.get("category")
        str_date = self.request.get("date")
        year, month, day = map(int, str_date.split('-'))
        new_date = datetime.date(year, month, day)
        new_comment = self.request.get("comment")
        expense = Expense.get_by_id(int(expense_id))
        expense.description = new_description
        expense.cost = new_cost
        expense.date = new_date
        expense.category = category
        expense.comment = new_comment
        expense.put()
        return self.redirect_to("exp-list")


class TotalExpensesHandler(BaseHandler):
    def get(self):
        if not_logged_in():
            return webapp2.redirect('/')
        user = users.get_current_user()
        expenses = Expense.query(Expense.user == user.user_id()).fetch()
        return self.render_template("total_expenses.html", {"expenses": expenses})


class ShowExpensesHandler(BaseHandler):
    def get(self):
        if not_logged_in():
            return webapp2.redirect('/')
        user = users.get_current_user()
        expenses = Expense.query(Expense.user == user.user_id()).fetch()
        categories = Category.query().fetch()
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        weekdays = ["Moh", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return self.render_template("show_expenses.html", {"expenses": expenses, "months": months,
                                                           "weekdays": weekdays, "categories": categories})


class DeleteExpenseHandler(BaseHandler):
    def get(self, expense_id):
        expense = Expense.get_by_id(int(expense_id))
        return self.render_template("delete_expense.html", {"expense": expense})

    def post(self, expense_id):
        expense = Expense.get_by_id(int(expense_id))
        expense.key.delete()
        return self.redirect_to("exp-list")


class AddCategoryHandler(BaseHandler):
    def get(self):
        if not_logged_in():
            return webapp2.redirect('/')
        categories = Category.query().fetch()
        return self.render_template("add_category.html", {"categories": categories})


class ResultCategoryHandler(BaseHandler):
    def post(self):
        category = self.request.get("category")
        new_category = Category(category=category)
        new_category.put()
        return self.render_template("category_added.html", {"new_category": new_category})


class EditCategoryHandler(BaseHandler):
    def get(self, category_id):
        category = Category.get_by_id(int(category_id))
        return self.render_template("edit_category.html", {"category": category})

    def post(self, category_id):
        category = Category.get_by_id(int(category_id))
        new_category = self.request.get("category")
        category.category = new_category
        category.put()
        return self.redirect_to("category-list")


class DeleteCategoryHandler(BaseHandler):
    def get(self, category_id):
        category = Category.get_by_id(int(category_id))
        return self.render_template("delete_category.html", {"category": category})

    def post(self, category_id):
        category = Category.get_by_id(int(category_id))
        category.key.delete()
        return self.redirect_to("exp-list")


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/add', AddExpenseHandler),
    webapp2.Route('/result', ResultHandler),
    webapp2.Route('/total_expenses', TotalExpensesHandler),
    webapp2.Route('/show_expenses', ShowExpensesHandler, name="exp-list"),
    webapp2.Route('/expense/<expense_id:\d+>/delete', DeleteExpenseHandler),
    webapp2.Route('/add_category', AddCategoryHandler, name="category-list"),
    webapp2.Route('/category/<category_id:\d+>/delete', DeleteCategoryHandler),
    webapp2.Route('/category_added', ResultCategoryHandler),
    webapp2.Route('/expense/<expense_id:\d+>/edit', EditExpenseHandler),
    webapp2.Route('/category/<category_id:\d+>/edit', EditCategoryHandler),
], debug=True)
