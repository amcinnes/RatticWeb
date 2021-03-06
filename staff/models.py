from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django import forms
from importloaders import keepass
from keepassdb.exc import AuthenticationError, InvalidDatabase


class UserForm(forms.ModelForm):
    # We want two password input boxes
    newpass = forms.CharField(widget=forms.PasswordInput, required=False, max_length=32, min_length=8)
    confirmpass = forms.CharField(widget=forms.PasswordInput, required=False, max_length=32, min_length=8)

    # Define our model
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'is_staff', 'groups')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Use checkboxes for groups
        # self.fields["groups"].widget = forms.CheckboxSelectMultiple()
        self.fields["groups"].widget = forms.SelectMultiple(attrs={'class': 'selectize-multiple'})
        self.fields["groups"].queryset = Group.objects.all()

    def clean(self):
        # Check the passwords given match
        cleaned_data = super(UserForm, self).clean()
        newpass = cleaned_data.get("newpass")
        confirmpass = cleaned_data.get("confirmpass")

        if newpass != confirmpass:
            msg = _('Passwords do not match')
            self._errors['confirmpass'] = self.error_class([msg])
            del cleaned_data['newpass']
            del cleaned_data['confirmpass']

        return cleaned_data


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name',)


class KeepassImportForm(forms.Form):
    file = forms.FileField()
    password = forms.CharField(max_length=50)
    group = forms.ModelChoiceField(queryset=Group.objects.all())

    def __init__(self, requser, *args, **kwargs):
        super(KeepassImportForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = Group.objects.filter(user=requser)

    def clean(self):
        cleaned_data = super(KeepassImportForm, self).clean()

        try:
            db = keepass(cleaned_data['file'], cleaned_data['password'])
            cleaned_data['db'] = db
        except AuthenticationError:
            msg = _('Could not read keepass file, the password you gave may not be correct.')
            self._errors['file'] = self.error_class([msg])
            del cleaned_data['file']
            del cleaned_data['password']
        except InvalidDatabase:
            msg = _('That file does not appear to be a valid KeePass file.')
            self._errors['file'] = self.error_class([msg])
            del cleaned_data['file']
            del cleaned_data['password']

        return cleaned_data
