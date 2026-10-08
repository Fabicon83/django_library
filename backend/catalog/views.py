from django.shortcuts import render


def hello(request):
    return render(
        request,
        "catalog/hello.html",
        {"name": "Fabiano 2.0", "html": "<b>Escape automatico</b>"},
    )
