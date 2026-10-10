from django import forms


class LendForm(forms.Form):
    barcode = forms.CharField(label="Codice a barre della copia", max_length=20)
    card_number = forms.CharField(label="Tessera del lettore", max_length=12)


class ReturnForm(forms.Form):
    barcode = forms.CharField(label="Codice a barre della copia", max_length=20)
