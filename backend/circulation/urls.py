from django.urls import path

from . import views

app_name = "circulation"

urlpatterns = [
    path("miei-prestiti/", views.MyLoansView.as_view(), name="my_loans"),
    path("banco/", views.LendView.as_view(), name="desk"),
    path("banco/restituzione/", views.ReturnView.as_view(), name="return"),
    path("miei-prestiti/rinnovo/", views.RenewView.as_view(), name="renew"),
]
